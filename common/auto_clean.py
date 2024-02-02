from util import db
from common.app_shadow import placeholder_app


class AutoClean:

    @staticmethod
    def clean_message():
        """清理过期消息"""
        from app.message.dao import dao
        with placeholder_app.app_context():
            dao.clean_timeout_message()
            db.session.commit()
