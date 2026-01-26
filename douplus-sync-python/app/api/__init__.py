"""
API模块 - 三层解耦架构

按照功能职责拆分：
- auth_api: 认证层 - 用户登录、用户信息
- sync_api: 同步层 - 订单采集、历史同步
- stats_api: 统计层 - 数据聚合、后台任务
- query_api: 查询层 - 前端查询、数据展示
- account_api: 账号管理 - 账号CRUD、授权
- order_api: 订单操作 - 订单续费、取消
"""

from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
sync_bp = Blueprint('sync', __name__, url_prefix='/api/douplus')
stats_bp = Blueprint('stats', __name__, url_prefix='/api/douplus')
query_bp = Blueprint('query', __name__, url_prefix='/api/douplus')
account_bp = Blueprint('account', __name__, url_prefix='/api')
order_bp = Blueprint('order', __name__, url_prefix='/api/douplus')

# 导入各模块的路由（在模块中注册）
from . import auth_api
from . import sync_api
from . import stats_api
from . import query_api
from . import account_api
from . import order_api

def register_blueprints(app):
    """注册所有API蓝图"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(order_bp)
