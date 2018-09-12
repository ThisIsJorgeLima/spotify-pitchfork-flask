# spotify-pitchfork-engine

Hosted on PythonAnywhere: [http://dianaxie.pythonanywhere.com](http://dianaxie.pythonanywhere.com)

A recommendation engine that takes a user's top 50 most-played tracks from the past few months
 and recommends a music critic to follow.

 This Flask app makes a user-authorized call to the Spotify API, interfaces the results
 with a hosted database in real-time, and returns an output.

 Based on my project [here](https://github.com/diana-xie/spotify_pitchfork_recommendations).

<i>Tools used: Flask, Bootstrap, HTML, CSS, Python, SQLite</i>

# how it works
All music critics are from Pitchfork and drawn from a cleaned and wrangled version of a
 Kaggle dataset of [Pitchfork reviews from 1999-2017](https://www.kaggle.com/nolanbconaway/pitchfork-data)
  (author: Nolan Conaway). Critic recommendations are based on similar music profiles,
 which are generated for both critic and user based on Spotify API's
 [audio features](https://developer.spotify.com/documentation/web-api/reference/tracks/get-audio-features/).

See [here](http://dianaxie.pythonanywhere.com/howitworks) for more details.

## credit

This code was based on the following repositories:
 - https://github.com/mari-linhares/spotify-flask - a much-appreciated guide for organizing and coding a Flask app that could
make authorized Spotify API calls, with flexibility between Python 2 and 3
- https://github.com/siquick/mostplayed - an example of a Flask app that could make Spotify API calls
requiring the "user" authorization [scope](https://developer.spotify.com/documentation/general/guides/scopes/),
followed by displayed results



