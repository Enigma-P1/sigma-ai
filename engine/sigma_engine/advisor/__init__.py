"""The Layer 2 advisor (PLAN §5): API client, context assembler, and the
routes/settings surface built on top of them. Layer 2 is optional end to
end -- nothing in `sigma_engine.advisor` runs unless a route in
routes/advisor.py is called, and every entry point here degrades to a
typed "unavailable" result rather than an exception when no API key is
configured (client.py's AdvisorUnavailable). Layer 1 (every other package
in sigma_engine) never imports anything from this package.
"""

from __future__ import annotations
