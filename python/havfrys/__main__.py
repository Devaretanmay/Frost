"""Allow ``python -m havfrys`` to invoke the CLI."""
from havfrys.cli import main
import sys

sys.exit(main())
