# altium_db_gui

## Making installer work with mariadb package

Replace mariadb/cursors.py line 22 

from mariadb.constants import *

to

from mariadb.constants import CLIENT
from mariadb.constants import CURSOR
from mariadb.constants import FIELD_TYPE
from mariadb.constants import FIELD_FLAG
from mariadb.constants import INDICATOR
from mariadb.constants import STATUS
from mariadb.constants import ERR