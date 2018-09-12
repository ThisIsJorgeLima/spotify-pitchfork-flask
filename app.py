from flask import Flask, request, redirect, render_template, session, make_response
from spotify_requests import spotify
import os


app = Flask(__name__)
app.secret_key = 'some key for session'


@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():
    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header
    return profile()


def valid_token(resp):
    return resp is not None and not 'error' in resp


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/go', methods=['GET', 'POST'])
def go():
    session.clear()
    session['num_tracks'] = '50'  # number of tracks to grab
    session['time_range'] = 'medium_term'  # time range of query:
    # https://developer.spotify.com/documentation/web-api/reference/personalization/get-users-top-artists-and-tracks/
    base_url = spotify.AUTH_URL
    response = make_response(redirect(base_url), 302)
    return response


@app.route('/profile')  # results page (w/ recommendation & user's top 50 tracks)
def profile():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        track_list, track_ids = spotify.get_users_top(auth_header, 'tracks')
        best_critic = spotify.get_audio_features(auth_header, track_ids)
        return render_template("done.html", track_list=track_list, best_critic=best_critic)
    return render_template('done.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/howitworks')
def howitworks():
    return render_template('howitworks.html')


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="127.0.0.1", port=port, debug=True)