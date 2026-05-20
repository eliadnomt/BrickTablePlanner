"""
Seating optimiser for the LEGO wedding seating chart generator.

Constraints handled:

* **Related guests stay together.** Two guests are treated as related only when
  the relationship is *mutual* — both list each other in ``related_guests``.
  Mutual relationships are transitive (A&B and B&C mutual ⇒ A, B and C share a
  table), so the result is the connected components of the *mutual* relationship
  graph. (A one-directional listing does not force two guests together; it is
  still honoured as a "nice to be next to" hint by the neighbour rule below.)
* **Single-language tables.** Guests at a table should share a common language so
  conversation flows. A guest who speaks several languages ("bilingual") can join
  any of their language groups.
* **Even tables.** Within each language group, guests are spread across the
  minimum number of tables as evenly as possible (no near-empty straggler
  tables).
* **Neighbour rule.** Every guest must, on each side, have a neighbour who is
  either related to them (in either direction) or shares a language with them.

If those constraints cannot all be satisfied, :func:`optimize_seating` returns a
:class:`SeatingResult` with ``feasible=False`` and a list of human-readable
``violations`` describing exactly which placements break a constraint. The UI
turns that list into a dialog box; the CLI prints it to stderr.

Adjacency convention
--------------------
Tables are round and seat :data:`SEATS_PER_TABLE` guests. When a table is full
its guests form a closed circle (the first and last guests are neighbours). When
a table is only partly filled, the empty seats break the circle, so the guests
form a line instead.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

SEATS_PER_TABLE = 10


@dataclass
class SeatingResult:
    tables: list = field(default_factory=list)  # list[list[Guest]] in seating order
    feasible: bool = True
    violations: list = field(default_factory=list)  # list[str]
    seats_per_table: int = SEATS_PER_TABLE

    @property
    def table_count(self) -> int:
        return len(self.tables)


# --------------------------------------------------------------------------- #
# Relationship helpers
# --------------------------------------------------------------------------- #

def _names_lower(values):
    return {str(v).lower() for v in values}


def _are_related(a, b) -> bool:
    """Lenient: a one-directional listing in either direction counts."""
    return (b.name.lower() in _names_lower(a.related)) or (
        a.name.lower() in _names_lower(b.related)
    )


def _mutually_related(a, b) -> bool:
    """Strict: both guests list each other."""
    return (b.name.lower() in _names_lower(a.related)) and (
        a.name.lower() in _names_lower(b.related)
    )


def _share_language(a, b) -> bool:
    return bool(a.language_set() & b.language_set())


def _compatible(a, b) -> bool:
    return _are_related(a, b) or _share_language(a, b)


def related_components(guests) -> list:
    """Connected components of the *mutual* relationship graph.

    Guests not mutually related to anyone become singleton components. The
    components are returned in order of first appearance in ``guests``.
    """
    guests = list(guests)
    n = len(guests)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    name_to_index = {g.name.lower(): i for i, g in enumerate(guests)}
    for i, guest in enumerate(guests):
        for related_name in guest.related:
            j = name_to_index.get(related_name.lower())
            if j is not None and j != i and _mutually_related(guest, guests[j]):
                union(i, j)

    grouped = {}
    order = []
    for i, guest in enumerate(guests):
        root = find(i)
        if root not in grouped:
            grouped[root] = []
            order.append(root)
        grouped[root].append(guest)
    return [grouped[root] for root in order]


def common_languages(guest_group) -> list:
    """Languages spoken by *every* guest in the group.

    Returns them in the casing/order used by the first guest. Empty list if the
    group has no language in common.
    """
    group = list(guest_group)
    if not group:
        return []
    intersection = set.intersection(*[g.language_set() for g in group])
    if not intersection:
        return []
    return [l for l in group[0].languages if l.lower() in intersection]


# --------------------------------------------------------------------------- #
# Neighbour-rule validation
# --------------------------------------------------------------------------- #

def _table_adjacent_pairs(n, seats_per_table):
    if n <= 1:
        return []
    pairs = [(i, i + 1) for i in range(n - 1)]
    if n >= 3 and n == seats_per_table:
        pairs.append((n - 1, 0))
    return pairs


def validate_seating(tables, seats_per_table=SEATS_PER_TABLE) -> list:
    """Check the neighbour rule for an arrangement.

    Returns a list of violation messages: one per adjacent pair of guests who
    are neither related nor share a language. An empty list means the
    arrangement satisfies the rule.
    """
    violations = []
    for table_index, table in enumerate(tables, start=1):
        guests = list(table)
        for a, b in _table_adjacent_pairs(len(guests), seats_per_table):
            ga, gb = guests[a], guests[b]
            if _compatible(ga, gb):
                continue
            violations.append(
                f"Table {table_index}: {ga.name} and {gb.name} are seated next to "
                f"each other but are not related and share no common language."
            )
    return violations


# --------------------------------------------------------------------------- #
# Ordering within a table
# --------------------------------------------------------------------------- #

def _edge_weight(a, b) -> int:
    """How strongly two guests "want" to sit next to each other."""
    if _mutually_related(a, b):
        return 3
    if _are_related(a, b):
        return 2
    if _share_language(a, b):
        return 1
    return 0


def _order_component(component) -> list:
    """Order one related component for seating.

    The component is, by construction, connected through *mutual* relationships
    (e.g. couples, families). The walk follows the strongest link available at
    each step — a mutual relationship before a one-directional one before a
    shared language — so couples and other mutually-related pairs end up next to
    each other instead of being split by an unrelated same-language guest. It
    starts at an "end" of the mutual sub-graph (e.g. one partner of an end
    couple in a chain of couples).
    """
    guests = list(component)
    n = len(guests)
    if n <= 2:
        return guests

    weight = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            w = _edge_weight(guests[i], guests[j])
            weight[i][j] = weight[j][i] = w

    mutual_degree = [sum(1 for j in range(n) if weight[i][j] == 3) for i in range(n)]
    compat_degree = [sum(1 for j in range(n) if weight[i][j] > 0) for i in range(n)]

    current = min(
        range(n),
        key=lambda i: (mutual_degree[i] if mutual_degree[i] else 10 ** 6,
                       compat_degree[i], i),
    )
    visited = [False] * n
    visited[current] = True
    order = [current]

    for _ in range(n - 1):
        def remaining_degree(j):
            return sum(1 for k in range(n) if not visited[k] and weight[j][k] > 0)

        nxt = min(
            (j for j in range(n) if not visited[j]),
            key=lambda j: (-weight[current][j], remaining_degree(j), j),
        )
        visited[nxt] = True
        order.append(nxt)
        current = nxt

    return [guests[i] for i in order]


def _order_table(components, closed=False) -> list:
    """Flatten a table's components into a seating order.

    Members of a related group stay contiguous (so they end up side by side, at
    worst across a corner). The components are then chained greedily so each
    junction joins two guests who are related (in either direction) or share a
    language, keeping any cross-group relationships adjacent.

    When ``closed`` is true (a full table — the last seat is next to the first)
    we additionally try to "close the ring": if the wrap-around pair would be
    incompatible we look for a component boundary at which reversing the tail
    makes both the wrap and the new junction compatible, and apply it. (If no
    such ordering exists, the wrap pair is left as is and ``validate_seating``
    will report it.)
    """
    sequences = [_order_component(c) for c in components]
    if not sequences:
        return []
    if len(sequences) == 1 and not closed:
        return list(sequences[0])

    chain = list(sequences.pop(0))
    boundaries = [len(chain)]  # start index of each subsequent component
    while sequences:
        last = chain[-1]
        pick = None  # (index, reversed)
        for relation_only in (True, False):
            for i, seq in enumerate(sequences):
                if (_are_related(last, seq[0]) if relation_only else _compatible(last, seq[0])):
                    pick = (i, False)
                    break
                if (_are_related(last, seq[-1]) if relation_only else _compatible(last, seq[-1])):
                    pick = (i, True)
                    break
            if pick is not None:
                break
        if pick is None:
            pick = (0, False)
        index, reverse = pick
        seq = sequences.pop(index)
        chain.extend(reversed(seq) if reverse else seq)
        boundaries.append(len(chain))

    if closed and len(chain) >= 3 and not _compatible(chain[-1], chain[0]):
        for b in boundaries[:-1]:  # candidate "reverse the tail from here" cuts
            if b == 0:
                continue
            if _compatible(chain[b - 1], chain[-1]) and _compatible(chain[b], chain[0]):
                chain = chain[:b] + chain[b:][::-1]
                break

    return chain


# --------------------------------------------------------------------------- #
# Balanced bin packing
# --------------------------------------------------------------------------- #

def _balanced_pack(components, seats_per_table) -> list:
    """Pack atomic components into as few tables as possible, balancing loads.

    Returns a list of tables, each a list of components. Uses a least-loaded
    (LPT-style) assignment so guests spread evenly; the table count only grows
    beyond ``ceil(total / seats)`` when large atomic components cannot be split.
    """
    comps = sorted(components, key=len, reverse=True)
    if not comps:
        return []
    total = sum(len(c) for c in comps)
    k = max(1, math.ceil(total / seats_per_table))

    while True:
        loads = [0] * k
        bins = [[] for _ in range(k)]
        ok = True
        for component in comps:
            candidates = [i for i in range(k) if loads[i] + len(component) <= seats_per_table]
            if not candidates:
                ok = False
                break
            i = min(candidates, key=lambda i: (loads[i], i))
            bins[i].append(component)
            loads[i] += len(component)
        if ok:
            return [b for b in bins if b]
        k += 1


# --------------------------------------------------------------------------- #
# Optimiser
# --------------------------------------------------------------------------- #

def optimize_seating(guests, seats_per_table=SEATS_PER_TABLE, max_tables=None) -> SeatingResult:
    """Assign guests to tables honouring the related / language constraints.

    Parameters
    ----------
    guests:
        Iterable of :class:`guests.Guest`.
    seats_per_table:
        Seats around each table (the LEGO model uses 10).
    max_tables:
        Optional cap on the number of tables the chosen layout can hold.

    Returns
    -------
    SeatingResult
        ``feasible`` is True only if no violations were detected. ``tables`` is
        always populated (best effort) so the UI can still show the attempt.
    """
    guests = list(guests)
    if not guests:
        return SeatingResult(tables=[], feasible=True, violations=[],
                             seats_per_table=seats_per_table)

    violations = []
    components = related_components(guests)

    oversized = [c for c in components if len(c) > seats_per_table]
    for component in oversized:
        names = ", ".join(g.name for g in component)
        violations.append(
            f"Related group ({names}) has {len(component)} guests, but a table "
            f"seats only {seats_per_table}; they cannot all sit together."
        )

    packable = [c for c in components if len(c) <= seats_per_table]

    # Components with no common language can only be seated on their own table.
    mixed = [c for c in packable if not common_languages(c)]
    flexible = [c for c in packable if common_languages(c)]

    # Assign each flexible component a single language. Components that only have
    # one possible language are forced; the rest go to whichever of their
    # languages currently has the least demand (load balancing).
    demand = defaultdict(int)
    forced = []
    deferred = []
    for component in flexible:
        options = [l.lower() for l in common_languages(component)]
        if len(options) == 1:
            forced.append((component, options[0]))
            demand[options[0]] += len(component)
        else:
            deferred.append((component, options))

    assignment = list(forced)
    for component, options in sorted(deferred, key=lambda t: len(t[0]), reverse=True):
        chosen = min(options, key=lambda lang: (demand[lang], lang))
        assignment.append((component, chosen))
        demand[chosen] += len(component)

    by_language = defaultdict(list)
    for component, lang in assignment:
        by_language[lang].append(component)

    table_components = []
    for lang in by_language:
        table_components.extend(_balanced_pack(by_language[lang], seats_per_table))
    for component in mixed:
        table_components.append([component])

    ordered_tables = []
    for components in table_components:
        size = sum(len(c) for c in components)
        ordered_tables.append(_order_table(components, closed=(size == seats_per_table)))

    # Oversized components: spread their members across extra tables (best effort).
    for component in oversized:
        members = list(component)
        for start in range(0, len(members), seats_per_table):
            ordered_tables.append(members[start:start + seats_per_table])

    if max_tables is not None and len(ordered_tables) > max_tables:
        violations.append(
            f"This guest list needs {len(ordered_tables)} tables, but the chosen "
            f"layout only supports {max_tables}. Reduce the guest count or pick a "
            f"layout that allows more tables."
        )

    violations.extend(validate_seating(ordered_tables, seats_per_table=seats_per_table))

    seen = set()
    unique_violations = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            unique_violations.append(v)

    return SeatingResult(
        tables=ordered_tables,
        feasible=not unique_violations,
        violations=unique_violations,
        seats_per_table=seats_per_table,
    )
