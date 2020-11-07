from unittest.mock import Mock, patch

import pytest

from osuapi import OsuMod
from praw.exceptions import RedditAPIException, RedditErrorItem

from src.worker import ReplyWith, reddit

from .. import has_osu_api_creds, mock_with_name


OSUBOT_COMMENT = """\
#### [Blind Stare - Shotgun Symphony+ [Impossibly Intense]](https://osu.ppy.sh/b/32570?m=0) [(&#x2b07;)](https://osu.ppy.sh/d/7671 "Download this beatmap") by [awp](https://osu.ppy.sh/u/2650 "30 ranked, 0 qualified, 0 loved, 2 unranked") || osu!standard
**#1: [Woey](https://osu.ppy.sh/u/3792472 "11,998pp - rank #345 (#56 US) - 99.26% accuracy - 342,867 playcount") (+HD - 99.86% - 335pp) || 1,337x max combo || Ranked (2009) || 422,642 plays**

|       | CS  | AR | OD | HP | SR   | BPM | Length | pp (95% &#124; 98% &#124; 99% &#124; 100%) |
:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:
| NoMod | 7   | 8  | 8  | 6  | 5.91 | 362 | 05:04  | 232 &#124; 260 &#124; 276 &#124; 296       |
| +EZ   | 3.5 | 4  | 4  | 3  | 4.65 | 362 | 05:04  | 103 &#124; 109 &#124; 113 &#124; 117       |

| Player                                                                 | Rank                    | pp     | Accuracy | Playstyle | Playcount | Top Play                                                                                                                                                                                                                                                                                     |
:-:|:-:|:-:|:-:|:-:|:-:|:-:
| [EZChamp](https://osu.ppy.sh/u/1719471 "Previously known as 'jakegc'") | #880&nbsp;(#29&nbsp;GB) | 10,475 | 97.93%   | TB+KB     | 53,129    | [KK&nbsp;&#x2011;&nbsp;Hidamari&nbsp;no&nbsp;Uta&nbsp;remake&nbsp;ver.&nbsp;[Cellina&nbsp;x&nbsp;Satellite's&nbsp;Bittersweet&nbsp;Memories]](https://osu.ppy.sh/b/2067473?m=0 "SR8.84 - CS2 - AR7.3 - OD7.1 - HP2 - 204BPM - 03:36") +EZHDDT&nbsp;&#124;&nbsp;92.16%&nbsp;&#124;&nbsp;784pp |

***

^(Ye XD – )[^Source](https://github.com/christopher-dG/osu-bot)^( | )[^Developer](https://reddit.com/u/PM_ME_DOG_PICS_PLS) [&nbsp;](http://x "Beatmap: Found in events
.osu: Downloaded from S3")
"""  # noqa: E501


@pytest.mark.skipif(not has_osu_api_creds(), reason="Needs osu! API key")
def test_parse_comment_e2e():
    osubot = Mock(
        body=OSUBOT_COMMENT,
        author=mock_with_name("osu-bot"),
        is_root=True,
        submission=Mock(title="TITLE", comments=[]),
    )
    trigger = Mock(
        body="a u/osu-bot record b",
        author=mock_with_name("not-osu-bot"),
        is_root=False,
        submission=Mock(title="TITLE", comments=[osubot]),
    )
    for comment in [osubot, trigger]:
        mapset, score, title = reddit.parse_comment(comment)
        assert mapset == 7671
        assert score == 3282835679
        assert title == "TITLE"


@patch("src.worker.reddit._edit_osubot_comment")
@patch("src.worker.reddit.is_osubot_comment", side_effect=[True, False])
@patch("src.worker.reddit.reply")
def test_success(reply, is_osubot_comment, edit_osubot_comment):
    reddit.success(1, "a")
    reply.assert_not_called()
    edit_osubot_comment.assert_called_with(1, "a")
    reddit.success(2, "b")
    reply.assert_called_with(2, "Here you go: b")


def test_reply():
    comment = Mock()
    reddit.reply(comment, "foo")
    comment.reply.assert_called_with("foo")
    ex = RedditAPIException([RedditErrorItem("a", "b"), RedditErrorItem("c", "d")])
    comment.reply.side_effect = ex
    with pytest.raises(RedditAPIException):
        reddit.reply(comment, "bar")
    ex.items[-1].error_type = "DELETED_COMMENT"
    reddit.reply(comment, "bar")


@patch("src.worker.reddit.is_osubot_comment", side_effect=[True, False])
@patch("src.worker.reddit.reply")
def test_failure(reply, is_osubot_comment):
    reddit.failure(1)
    reply.assert_not_called()
    reddit.failure(2)
    reply.assert_called_with(2, "Sorry, something unexpected went wrong.")


def test_finished():
    comment = Mock()
    reddit.finished(comment)
    comment.save.assert_called_with()


@patch("src.worker.reddit.is_osubot_comment", return_value=True)
def test_find_osubot_comment(is_osubot_comment):
    assert reddit._find_osubot_comment(1) == 1
    is_osubot_comment.return_value = False
    with pytest.raises(ReplyWith, match="couldn't find a /u/osu-bot comment"):
        reddit._find_osubot_comment(Mock(submission=Mock(comments=[2, 3, 4])))
    is_osubot_comment.side_effect = [False, False, True]
    assert reddit._find_osubot_comment(Mock(submission=Mock(comments=[5, 6, 7]))) == 6


@patch("src.worker.reddit._parse_beatmap", return_value=1)
@patch("src.worker.reddit._get_mapset", return_value=2)
@patch("src.worker.reddit._parse_player", return_value=3)
@patch("src.worker.reddit._parse_mods", return_value=4)
@patch("src.worker.reddit._check_not_unranked")
@patch("src.worker.reddit._check_standard")
def test_parse_osubot_comment(
    check_standard,
    check_not_unranked,
    parse_mods,
    parse_player,
    get_mapset,
    parse_beatmap,
):
    assert reddit._parse_osubot_comment("foo\nbar") == (2, 1, 3, 4)
    lines = ["foo", "bar"]
    parse_beatmap.assert_called_with(lines)
    get_mapset.assert_called_with(1)
    parse_player.assert_called_with(lines)
    parse_mods.assert_called_with(lines)
    check_not_unranked.assert_called_with(lines)
    check_standard.assert_called_with(lines)


def test_parse_beatmap():
    with pytest.raises(ReplyWith, match="couldn't find the beatmap"):
        reddit._parse_beatmap(["foo", "bar"])
    assert reddit._parse_beatmap(["a (https://osu.ppy.sh/b/1) b", "foo"]) == 1


@patch("src.worker.reddit.OSU_API")
def test_get_mapset(osu_api):
    osu_api.get_beatmaps.side_effect = [[], [Mock(beatmapset_id=1)]]
    with pytest.raises(ReplyWith, match="couldn't find the mapset"):
        reddit._get_mapset(1)
    osu_api.get_beatmaps.assert_called_with(beatmap_id=1)
    assert reddit._get_mapset(2) == 1


def test_parse_player():
    lines = ["x" for i in range(20)]
    with pytest.raises(ReplyWith, match="couldn't find the player"):
        reddit._parse_player(lines)
    lines[10] = "a (https://osu.ppy.sh/u/1) b"
    assert reddit._parse_player(lines) == 1


def test_parse_mods():
    lines = ["x" for i in range(20)]
    assert reddit._parse_mods(lines) == 0
    lines[6] = "|   +HDDT   |"
    assert reddit._parse_mods(lines) == 72


def test_check_not_unranked():
    with pytest.raises(ReplyWith, match="can't record replays for unranked"):
        reddit._check_not_unranked(["a", "foo bar baz || Unranked"])
    reddit._check_not_unranked(["foo", "bar"])


def test_check_standard():
    with pytest.raises(ReplyWith, match="can only record osu!standard"):
        reddit._check_standard(["foo", "bar"])
    reddit._check_standard(["a osu!standard b", "bar"])
    reddit._check_standard(["foo", "a osu!standard b"])


@patch("src.worker.reddit.OSU_API")
def test_score_id(osu_api):
    osu_api.get_scores.side_effect = [
        [],
        [Mock(replay_available=False)],
        [Mock(replay_available=True, score_id=1)],
    ]
    with pytest.raises(ReplyWith, match="couldn't find the replay"):
        reddit._score_id(1, 2, 3)
    osu_api.get_scores.assert_called_with(1, username=2, mods=OsuMod(3))
    with pytest.raises(ReplyWith, match="not available"):
        reddit._score_id(4, 5, 6)
    assert reddit._score_id(7, 8, 9) == 1


@patch("src.worker.reddit.logging.info")
@patch("src.worker.reddit._find_osubot_comment", side_effect=lambda x: x)
def test_edit_osubot_comment(find_osubot_comment, info):
    before = "a\n\nb\n\n***\n\nc"
    comment = Mock(body=before)

    def add_to_body():
        comment.body += "[Streamable replay](A)"

    comment.refresh = add_to_body
    reddit._edit_osubot_comment(comment, "A")
    info.assert_not_called()
    comment.edit.assert_not_called()
    comment.body = before
    reddit._edit_osubot_comment(comment, "B")
    info.assert_called_with("Duplicate video should be deleted: B")
    comment.edit.assert_not_called()
    comment.body = before
    comment.refresh = lambda: None
    reddit._edit_osubot_comment(comment, "C")
    comment.edit.assert_called_with("a\n\nb\n\n[Streamable replay](C)\n\n***\n\nc")
