"""Allow ``python -m frost`` to invoke the CLI."""
from frost.cli import main
import sys

sys.exit(main())
