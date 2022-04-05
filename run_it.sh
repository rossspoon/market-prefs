export OTREE_ADMIN_PASSWORD=b9rry@
export OTREE_PRODUCTION=1 # uncomment this line to enable production mode
#export OTREE_AUTH_LEVEL=DEMO
export DATABASE_URL=postgres://postgres@localhost/DATABASE

otree resetdb
otree prodserver 192.168.1.135:8000
#brew services start postgresql
#usr/local/opt/postgres/bin/createuser -s postgres
#brew services stop postgresql

unset DATABASE_URL


