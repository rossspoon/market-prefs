set OTREE_ADMIN_PASSWORD=b9rry@
set OTREE_AUTH_LEVEL=1 

REM Comment out this line to turn on debug mode
set OTREE_PRODUCTION=1 

REM Change this to control access
set OTREE_AUTH_LEVEL=STUDY
REM set OTREE_AUTH_LEVEL=DEMO


set DATABASE_URL=postgres://vteconlab:econvt!@localhost/squeeze


REM otree resetdb
otree prodserver econlabhost18s:8000
