"""${message}

Revision ID: ${up_revision}
Revises:${" " + (down_revision | comma,n) if down_revision else ""}
Create Date: ${create_date}

"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """执行升级操作"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """执行回滚操作"""
    ${downgrades if downgrades else "pass"}
