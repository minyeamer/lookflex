import enum


class Role(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GroupType(str, enum.Enum):
    DEPARTMENT = "DEPARTMENT"
    POSITION = "POSITION"
    CUSTOM = "CUSTOM"


class DSSourceType(str, enum.Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    MSSQL = "MSSQL"
    BIGQUERY = "BIGQUERY"
    EXCEL = "EXCEL"
    CSV = "CSV"


class FieldType(str, enum.Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class AggregateType(str, enum.Enum):
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    NONE = "NONE"


class ChartType(str, enum.Enum):
    TABLE = "TABLE"
    PIVOT = "PIVOT"
    LINE = "LINE"
    BAR = "BAR"
    STACKED_BAR = "STACKED_BAR"
    PIE = "PIE"
    SCORECARD = "SCORECARD"


class FilterType(str, enum.Enum):
    DROPDOWN = "DROPDOWN"
    TEXT_INPUT = "TEXT_INPUT"
    RANGE = "RANGE"
    DATE_RANGE = "DATE_RANGE"


class FilterOp(str, enum.Enum):
    EQ = "EQ"
    NEQ = "NEQ"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    REGEX = "REGEX"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"


class SortDir(str, enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class CondFormatApplyTo(str, enum.Enum):
    CELL = "CELL"
    ROW = "ROW"


class NotificationType(str, enum.Enum):
    REGISTER_REQUEST = "REGISTER_REQUEST"
    REGISTER_APPROVED = "REGISTER_APPROVED"
    REGISTER_REJECTED = "REGISTER_REJECTED"


class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DATA_QUERY = "DATA_QUERY"
    EXPORT = "EXPORT"
    DASHBOARD_EDIT = "DASHBOARD_EDIT"
    DATASOURCE_EDIT = "DATASOURCE_EDIT"
    USER_EDIT = "USER_EDIT"
