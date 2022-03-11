from common.ParticipantFuctions import generate_participant_ids

prices = [-1, 3000, 2500, 1400]
volumes = [-1, 12, 18, 8]
dividends = [-1, 40, 100, 40]


def creating_session(subsession):
    round_number = subsession.round_number

    # Stuff for all rounds
    subsession.is_practice = True
    for g in subsession.get_groups():
        g.float = 10
        g.short = 5
        g.is_practice = True
        g.price = prices[round_number]
        g.volume = volumes[round_number]
        g.dividend = dividends[round_number]

    for p in subsession.get_players():
        p.is_practice = True

    # only set up endowments in the first round
    if round_number != 1:
        return

    generate_participant_ids(subsession)
    session = subsession.session
    for p in subsession.get_players():
        p.cash = 10000
        p.shares = 2
