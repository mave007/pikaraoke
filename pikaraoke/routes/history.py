from flask import Blueprint, flash, render_template, request

from pikaraoke.lib.current_app import get_karaoke_instance, is_admin

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():
    k = get_karaoke_instance()
    db = k.db
    limit = int(request.args.get("limit", 10))
    offset = int(request.args.get("offset", 0))
    date_filter = request.args.get("date")
    user_filter = request.args.get("user")

    # Top users parameters
    top_users_limit = int(request.args.get("users_limit", 10))
    top_users_offset = int(request.args.get("users_offset", 0))
    top_users_sort = request.args.get("users_sort", "count")
    top_users_order = request.args.get("users_order", "DESC")
    try:
        last_plays_full = db.get_last_plays(limit + 1, offset, date_filter, user_filter)
        has_more = len(last_plays_full) > limit
        last_plays = last_plays_full[:limit]

        # Calculate pagination info
        total_count = db.get_plays_count(date_filter, user_filter)
        current_page = (offset // limit) + 1
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        has_previous = current_page > 1
        has_next = has_more
        next_offset = offset + limit
        prev_offset = max(0, offset - limit)

        top_songs = db.get_top_songs(10)
        top_users = db.get_top_users(
            top_users_limit, top_users_offset, top_users_sort, top_users_order
        )

        # Calculate top users pagination info
        top_users_total_count = db.get_top_users_count()
        top_users_current_page = (top_users_offset // top_users_limit) + 1
        top_users_total_pages = (top_users_total_count + top_users_limit - 1) // top_users_limit
        top_users_has_previous = top_users_current_page > 1
        top_users_has_next = top_users_current_page < top_users_total_pages
        top_users_next_offset = top_users_offset + top_users_limit
        top_users_prev_offset = max(0, top_users_offset - top_users_limit)

        top_songs_today = db.get_top_songs_by_period("day", 10)
        top_songs_month = db.get_top_songs_by_period("month", 10)
        top_songs_year = db.get_top_songs_by_period("year", 10)
        distinct_users = db.get_distinct_users()
        distinct_dates = db.get_distinct_dates()
    except Exception as e:
        flash(f"Error loading history data: {str(e)}", "is-danger")
        top_songs = []
        top_users = []
        last_plays = []
        top_songs_today = []
        top_songs_month = []
        top_songs_year = []
        distinct_users = []
        distinct_dates = []
        total_count = 0
        current_page = 1
        total_pages = 1
        has_previous = False
        has_next = False
        next_offset = 0
        prev_offset = 0
        has_more = False
        top_users_total_count = 0
        top_users_current_page = 1
        top_users_total_pages = 1
        top_users_has_previous = False
        top_users_has_next = False
        top_users_next_offset = 0
        top_users_prev_offset = 0
    return render_template(
        "history.html",
        top_songs=top_songs,
        top_users=top_users,
        last_plays=last_plays,
        top_songs_today=top_songs_today,
        top_songs_month=top_songs_month,
        top_songs_year=top_songs_year,
        is_admin=is_admin(),
        limit=limit,
        offset=offset,
        has_more=has_more,
        next_offset=next_offset,
        total_count=total_count,
        current_page=current_page,
        total_pages=total_pages,
        has_previous=has_previous,
        has_next=has_next,
        prev_offset=prev_offset,
        top_users_limit=top_users_limit,
        top_users_offset=top_users_offset,
        top_users_sort=top_users_sort,
        top_users_order=top_users_order,
        top_users_total_count=top_users_total_count,
        top_users_current_page=top_users_current_page,
        top_users_total_pages=top_users_total_pages,
        top_users_has_previous=top_users_has_previous,
        top_users_has_next=top_users_has_next,
        top_users_next_offset=top_users_next_offset,
        top_users_prev_offset=top_users_prev_offset,
        date_filter=date_filter,
        user_filter=user_filter,
        distinct_users=distinct_users,
        distinct_dates=distinct_dates,
    )
