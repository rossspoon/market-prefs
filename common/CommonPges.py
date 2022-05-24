from otree.api import WaitPage


def wait_template_vars(player):
    num_players = len(player.group.get_players())
    part = player.participant
    page_num = part._index_in_pages

    cnt = 0
    for p in player.group.get_players():
        if p.participant._index_in_pages == page_num:
            cnt += 1

    pct = cnt / num_players
    pct_str = f"{pct:.0%}"
    return dict(N=num_players, cnt=cnt, pct=pct_str)


class UpdatedWaitPage(WaitPage):
    template_name = 'UpdatedWaitPage.html'
    title_text = "Waiting on Other Players"
    vars_for_template = wait_template_vars
