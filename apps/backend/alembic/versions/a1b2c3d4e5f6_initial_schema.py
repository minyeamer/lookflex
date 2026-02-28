"""initial schema

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-02-28 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum Types ────────────────────────────────────────────────────────────
    role_enum = postgresql.ENUM(
        "OWNER", "ADMIN", "EDITOR", "VIEWER", name="role", create_type=False
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    approval_status_enum = postgresql.ENUM(
        "PENDING", "APPROVED", "REJECTED", name="approvalstatus", create_type=False
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    group_type_enum = postgresql.ENUM(
        "DEPARTMENT", "POSITION", "CUSTOM", name="grouptype", create_type=False
    )
    group_type_enum.create(op.get_bind(), checkfirst=True)

    ds_source_type_enum = postgresql.ENUM(
        "POSTGRESQL", "MYSQL", "MSSQL", "BIGQUERY", "EXCEL", "CSV",
        name="dssourcetype", create_type=False
    )
    ds_source_type_enum.create(op.get_bind(), checkfirst=True)

    field_type_enum = postgresql.ENUM(
        "TEXT", "NUMBER", "DATE", "DATETIME", "BOOLEAN",
        name="fieldtype", create_type=False
    )
    field_type_enum.create(op.get_bind(), checkfirst=True)

    aggregate_type_enum = postgresql.ENUM(
        "SUM", "AVG", "MIN", "MAX", "COUNT", "COUNT_DISTINCT", "NONE",
        name="aggregatetype", create_type=False
    )
    aggregate_type_enum.create(op.get_bind(), checkfirst=True)

    chart_type_enum = postgresql.ENUM(
        "TABLE", "PIVOT", "LINE", "BAR", "STACKED_BAR", "PIE", "SCORECARD",
        name="charttype", create_type=False
    )
    chart_type_enum.create(op.get_bind(), checkfirst=True)

    filter_type_enum = postgresql.ENUM(
        "DROPDOWN", "TEXT_INPUT", "RANGE", "DATE_RANGE",
        name="filtertype", create_type=False
    )
    filter_type_enum.create(op.get_bind(), checkfirst=True)

    filter_op_enum = postgresql.ENUM(
        "EQ", "NEQ", "CONTAINS", "NOT_CONTAINS", "STARTS_WITH", "ENDS_WITH",
        "REGEX", "GT", "GTE", "LT", "LTE", "BETWEEN", "IS_NULL", "IS_NOT_NULL",
        name="filterop", create_type=False
    )
    filter_op_enum.create(op.get_bind(), checkfirst=True)

    cond_format_apply_to_enum = postgresql.ENUM(
        "CELL", "ROW", name="condformatapplyto", create_type=False
    )
    cond_format_apply_to_enum.create(op.get_bind(), checkfirst=True)

    notification_type_enum = postgresql.ENUM(
        "REGISTER_REQUEST", "REGISTER_APPROVED", "REGISTER_REJECTED",
        name="notificationtype", create_type=False
    )
    notification_type_enum.create(op.get_bind(), checkfirst=True)

    audit_action_enum = postgresql.ENUM(
        "LOGIN", "LOGOUT", "DATA_QUERY", "EXPORT",
        "DASHBOARD_EDIT", "DATASOURCE_EDIT", "USER_EDIT",
        name="auditaction", create_type=False
    )
    audit_action_enum.create(op.get_bind(), checkfirst=True)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("OWNER", "ADMIN", "EDITOR", "VIEWER", name="role"), nullable=False),
        sa.Column("profile_image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── groups ────────────────────────────────────────────────────────────────
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.Enum("DEPARTMENT", "POSITION", "CUSTOM", name="grouptype"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", "type", name="uq_group_name_type"),
    )

    # ── user_group (M2M) ──────────────────────────────────────────────────────
    op.create_table(
        "user_group",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── register_requests ────────────────────────────────────────────────────
    op.create_table(
        "register_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("requested_role", sa.Enum("OWNER", "ADMIN", "EDITOR", "VIEWER", name="role"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="approvalstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("processed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_register_requests_email", "register_requests", ["email"])
    op.create_index("ix_register_requests_status", "register_requests", ["status"])

    # ── dashboards ────────────────────────────────────────────────────────────
    op.create_table(
        "dashboards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dashboards_owner_id", "dashboards", ["owner_id"])

    # ── pages ─────────────────────────────────────────────────────────────────
    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dashboard_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("width", sa.Integer(), nullable=False, server_default=sa.text("1920")),
        sa.Column("height", sa.Integer(), nullable=False, server_default=sa.text("1080")),
        sa.Column("background_color", sa.String(20), nullable=False, server_default=sa.text("'#ffffff'")),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_pages_dashboard_id", "pages", ["dashboard_id"])

    # ── dashboard_favorites ───────────────────────────────────────────────────
    op.create_table(
        "dashboard_favorites",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dashboard_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── page_favorites ────────────────────────────────────────────────────────
    op.create_table(
        "page_favorites",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── datasources ───────────────────────────────────────────────────────────
    op.create_table(
        "datasources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("POSTGRESQL", "MYSQL", "MSSQL", "BIGQUERY", "EXCEL", "CSV", name="dssourcetype"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("connection_config", postgresql.JSONB(), nullable=True),
        sa.Column("allow_all", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_id", name="uq_datasources_source_id"),
    )
    op.create_index("ix_datasources_source_id", "datasources", ["source_id"], unique=True)

    # ── datasource_fields ─────────────────────────────────────────────────────
    op.create_table(
        "datasource_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("datasource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_id", sa.String(200), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("type", sa.Enum("TEXT", "NUMBER", "DATE", "DATETIME", "BOOLEAN", name="fieldtype"), nullable=False),
        sa.Column(
            "default_aggregate",
            sa.Enum("SUM", "AVG", "MIN", "MAX", "COUNT", "COUNT_DISTINCT", "NONE", name="aggregatetype"),
            nullable=False,
            server_default="NONE",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("number_format", sa.String(100), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("datasource_id", "field_id", name="uq_datasource_field"),
    )
    op.create_index("ix_datasource_fields_datasource_id", "datasource_fields", ["datasource_id"])

    # ── datasource_permissions ────────────────────────────────────────────────
    op.create_table(
        "datasource_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("datasource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(10), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.UniqueConstraint("datasource_id", "entity_type", "entity_id", name="uq_ds_permission"),
    )
    op.create_index("ix_datasource_permissions_datasource_id", "datasource_permissions", ["datasource_id"])

    # ── charts ────────────────────────────────────────────────────────────────
    op.create_table(
        "charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("datasource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "type",
            sa.Enum("TABLE", "PIVOT", "LINE", "BAR", "STACKED_BAR", "PIE", "SCORECARD", name="charttype"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False, server_default=sa.text("''")),
        sa.Column("x", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("y", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("width", sa.Integer(), nullable=False, server_default=sa.text("400")),
        sa.Column("height", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("style", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_charts_page_id", "charts", ["page_id"])

    # ── chart_groups ──────────────────────────────────────────────────────────
    op.create_table(
        "chart_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_chart_groups_page_id", "chart_groups", ["page_id"])

    # ── chart_group_items ─────────────────────────────────────────────────────
    op.create_table(
        "chart_group_items",
        sa.Column("chart_group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chart_groups.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charts.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── filters ───────────────────────────────────────────────────────────────
    op.create_table(
        "filters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("datasource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("field_id", sa.String(200), nullable=True),
        sa.Column(
            "type",
            sa.Enum("DROPDOWN", "TEXT_INPUT", "RANGE", "DATE_RANGE", name="filtertype"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("y", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("width", sa.Integer(), nullable=False, server_default=sa.text("200")),
        sa.Column("height", sa.Integer(), nullable=False, server_default=sa.text("40")),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_filters_page_id", "filters", ["page_id"])

    # ── default_filter_rules ──────────────────────────────────────────────────
    op.create_table(
        "default_filter_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("apply_to", sa.String(200), nullable=False),
        sa.Column("datasource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_id", sa.String(200), nullable=False),
        sa.Column(
            "operator",
            sa.Enum(
                "EQ", "NEQ", "CONTAINS", "NOT_CONTAINS", "STARTS_WITH", "ENDS_WITH",
                "REGEX", "GT", "GTE", "LT", "LTE", "BETWEEN", "IS_NULL", "IS_NOT_NULL",
                name="filterop",
            ),
            nullable=False,
        ),
        sa.Column("value", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_default_filter_rules_page_id", "default_filter_rules", ["page_id"])

    # ── conditional_formats ───────────────────────────────────────────────────
    op.create_table(
        "conditional_formats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "apply_to",
            sa.Enum("CELL", "ROW", name="condformatapplyto"),
            nullable=False,
            server_default="CELL",
        ),
        sa.Column("target_fields", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_conditional_formats_chart_id", "conditional_formats", ["chart_id"])

    # ── conditional_format_rules ──────────────────────────────────────────────
    op.create_table(
        "conditional_format_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("format_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conditional_formats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "operator",
            sa.Enum(
                "EQ", "NEQ", "CONTAINS", "NOT_CONTAINS", "STARTS_WITH", "ENDS_WITH",
                "REGEX", "GT", "GTE", "LT", "LTE", "BETWEEN", "IS_NULL", "IS_NOT_NULL",
                name="filterop",
            ),
            nullable=False,
        ),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("second_value", postgresql.JSONB(), nullable=True),
        sa.Column("style", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_conditional_format_rules_format_id", "conditional_format_rules", ["format_id"])

    # ── user_view_configs ─────────────────────────────────────────────────────
    op.create_table(
        "user_view_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "chart_id", name="uq_user_chart_view"),
    )
    op.create_index("ix_user_view_configs_user_id", "user_view_configs", ["user_id"])
    op.create_index("ix_user_view_configs_chart_id", "user_view_configs", ["chart_id"])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "REGISTER_REQUEST", "REGISTER_APPROVED", "REGISTER_REJECTED",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link_url", sa.String(500), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # ── smtp_configs ──────────────────────────────────────────────────────────
    op.create_table(
        "smtp_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(254), nullable=True),
        sa.Column("encrypted_password", sa.String(500), nullable=True),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("from_name", sa.String(100), nullable=True),
        sa.Column("from_email", sa.String(254), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "LOGIN", "LOGOUT", "DATA_QUERY", "EXPORT",
                "DASHBOARD_EDIT", "DATASOURCE_EDIT", "USER_EDIT",
                name="auditaction",
            ),
            nullable=False,
        ),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # 역순으로 삭제 (FK 의존성 순서)
    op.drop_table("audit_logs")
    op.drop_table("smtp_configs")
    op.drop_table("notifications")
    op.drop_table("user_view_configs")
    op.drop_table("conditional_format_rules")
    op.drop_table("conditional_formats")
    op.drop_table("default_filter_rules")
    op.drop_table("filters")
    op.drop_table("chart_group_items")
    op.drop_table("chart_groups")
    op.drop_table("charts")
    op.drop_table("datasource_permissions")
    op.drop_table("datasource_fields")
    op.drop_table("datasources")
    op.drop_table("page_favorites")
    op.drop_table("dashboard_favorites")
    op.drop_table("pages")
    op.drop_table("dashboards")
    op.drop_table("register_requests")
    op.drop_table("user_group")
    op.drop_table("groups")
    op.drop_table("users")

    # Enum Types 삭제
    for enum_name in [
        "auditaction",
        "notificationtype",
        "condformatapplyto",
        "filterop",
        "filtertype",
        "charttype",
        "aggregatetype",
        "fieldtype",
        "dssourcetype",
        "grouptype",
        "approvalstatus",
        "role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
