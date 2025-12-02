from flask import Blueprint, flash, redirect, render_template, request, url_for

from pikaraoke.lib.current_app import get_karaoke_instance, is_admin

admin_history_bp = Blueprint("admin_history", __name__)


@admin_history_bp.route("/admin/history")
def admin_history():
    if not is_admin():
        return redirect(url_for("home.home"))
    k = get_karaoke_instance()
    db = k.db
    user_filter = request.args.get("user", "")
    date_filter = request.args.get("date", "")
    try:
        plays = db.get_plays_by_user(user_filter, date_filter)
        aliases = db.get_user_aliases()
        distinct_users = db.get_distinct_users()
        distinct_dates = db.get_distinct_dates()
        distinct_songs = db.get_distinct_songs()
    except Exception as e:
        flash(f"Error loading admin history data: {str(e)}", "is-danger")
        plays = []
        aliases = []
        distinct_users = []
        distinct_dates = []
        distinct_songs = []
    return render_template(
        "admin_history.html",
        plays=plays,
        aliases=aliases,
        selected_user=user_filter,
        selected_date=date_filter,
        distinct_users=distinct_users,
        distinct_dates=distinct_dates,
        distinct_songs=distinct_songs,
        is_admin=True,
    )


@admin_history_bp.route("/admin/history/update", methods=["POST"])
def update_play():
    if not is_admin():
        return redirect(url_for("home.home"))
    k = get_karaoke_instance()
    db = k.db
    play_id = request.form.get("play_id")
    user = request.form.get("user")
    song = request.form.get("song")
    try:
        db.update_play(play_id, user=user, song=song)
        flash("Play updated", "success")
    except Exception as e:
        flash(f"Error updating play: {str(e)}", "is-danger")
    return redirect(url_for("admin_history.admin_history"))


@admin_history_bp.route("/admin/history/alias", methods=["POST"])
def set_alias():
    if not is_admin():
        return redirect(url_for("home.home"))
    k = get_karaoke_instance()
    db = k.db
    alias = request.form.get("alias")
    canonical = request.form.get("canonical")
    try:
        db.set_user_alias(alias, canonical)
        flash("Alias set", "success")
    except Exception as e:
        flash(f"Error setting alias: {str(e)}", "is-danger")
    return redirect(url_for("admin_history.admin_history"))


@admin_history_bp.route("/admin/history/remove_alias", methods=["POST"])
def remove_alias():
    if not is_admin():
        return redirect(url_for("home.home"))
    k = get_karaoke_instance()
    db = k.db
    alias = request.form.get("alias")
    try:
        db.remove_user_alias(alias)
        flash("Alias removed", "success")
    except Exception as e:
        flash(f"Error removing alias: {str(e)}", "is-danger")
    return redirect(url_for("admin_history.admin_history"))
