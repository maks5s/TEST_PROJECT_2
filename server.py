# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from alembic.config import Config
from alembic import command
from main import TestApp
from queries.application import get_active_users_paginated
from pathlib2 import Path
from modules.logger import get_logger

app = Flask(__name__)

def run_migrations():
    """Alembic migration function."""
    print("Running migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations complete.")

test_app = TestApp()

@app.route('/active-users', methods=['GET'])
def active_users():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        users_data, total_count = get_active_users_paginated(
            test_app.session_factory,
            to_dict=True,
            page=page,
            per_page=per_page
        )

        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
            "status": "success",
            "metadata": {
                "current_page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages
            },
            "data": users_data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    logger = get_logger(
        log_file=Path('./logs').joinpath("application").resolve(),
        enable_stdout=True,
        log_level="DEBUG",
        use_colors=True,
    )

    try:
        run_migrations()

        test_app.alembic_setup()
        test_app.populate_users_in_db(count=100)

        app.run(host='0.0.0.0', port=5000)

    except RuntimeError as err:
        logger.exception(
            "Can not run application due to the error '{}'".format(err)
        )
