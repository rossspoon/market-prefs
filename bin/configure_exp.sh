#export LANDING_LIMIT=20
#export EXPERIMENT_URL=https://vt-market-experiment.herokuapp.com/room/market2?participant_label={}
#export SSE_NUM_ROUNDS=50

heroku config:set LANDING_LIMIT=20
heroku config:set SSE_NUM_ROUNDS=50
heroku config:set EXPERIMENT_URL=https://vt-market-experiment.herokuapp.com/room/market2?participant_label={}

