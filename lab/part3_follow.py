"""Part 3: Follow. TODO 5 (the rule that ends follow mode), then TODO 6 (the follow tool).

The person follower itself is provided (robot.set_following). The rule is yours:

    Questions and conversation keep following. Any motion (walk, turn, arc, trick,
    stand up, lie down) ends follow mode, and Pupper says so first:
    "Let me stop following you and ..."
"""

from __future__ import annotations

from robot_api import Result, Robot, Trick, not_written  # noqa: F401
from tool_registry import Param, tool


# ============================================================ what the robot does
async def prepare_to_move(robot: Robot) -> str:
    """Get the robot ready for a new motion. Every motion calls this first,
    before it queues anything: look for it in stand_up (basics.py) and walk
    (part2_walk.py).

    What it is for: stopping anything that runs on its own, outside the queue,
    and would fight with the new motion. In Gemini Pupper that is the person
    follower, so its one job is to end follow mode; it is also where anything
    like it you add later goes (a patrol loop, dancing to music). Getting the
    legs ready is a different job, done later in the job by switch_to.

    TODO 5 (Part 3) ------------------------------------------------------------
    The rule:            talking and questions keep following. Any motion (walk,
                         turn, trick, stand up, lie down) ends follow mode right
                         away, not when the queue gets to the motion.
    Returns:             a note that goes in front of the tool's reply, e.g.
                         "Stopped following the person first.", or "" if the
                         robot wasn't following.
    Why right away:      the person asked for something else *now*; the robot
                         shouldn't keep chasing them until the queue gets there.
    Why a note:          Gemini can only say "Let me stop following you and ..."
                         if the reply tells it.
    Use:                 robot.following, await robot.stop_following(),
                         robot.send_speed(0, 0, 0) (stand still)
    Tests check:         - stand_up, lie_down and walk stop the follower right
                           away, before the queue gets to them
                         - their reply contains the word "follow".
                           Passes: "Stopped following the person first. activate walking queued; ..."
                           Fails:  "Done. activate walking queued; ..."
                         - when not following, the reply does NOT contain "follow"
                         - robot_status (a question) keeps following
    Test:                python3 lab/test.py todo5
    """

    if not robot.following:
        return ""
    await robot.stop_following()
    robot.send_speed(0, 0, 0)
    return "Stopped following the person first."


# ============================================================ what Gemini reads
# TODO 6: describe follow for Gemini, and write its body: robot.set_following(enabled)
# (provided) starts or stops the person follower. Gemini should know what keeps
# follow mode on and what ends it (your rule in TODO 5).
#   Tests check:
#   - follow's description is 20+ characters, enabled is described, and the
#     description says what ends it: it contains "end" or "stop".
#     Passes: "... any motion tool (walk, turn, ...) ends it."  Fails: "Follow the person."
#   - prompt.md's Follow mode section contains "end" or "stop"
#   - follow(enabled=True) starts the follower, follow(enabled=False) stops it
#   Test: python3 lab/test.py todo6

@tool(
    "follow",
    "Start or stop follow mode: Pupper follows the nearest person, keeping its distance, "
    "walking in a straight line (it cannot go around furniture, so lead it around obstacles). "
    "Use it for 'follow me', 'come here' and 'stay with me', and with enabled=false for 'stop following'. "
    "Follow mode stays on while you talk, answer questions, or look at the camera "
    "('what do you see?'). Any motion tool (move, turn, arc, play_trick, stand_up, lie_down) "
    "ends follow mode, and the reply says so. Starting follow mode clears any queued moves. "
    "Pupper cannot follow while it is in a trick that walks in its own stance (the spider): "
    "the tool refuses, and Pupper has to stand up first.",
    enabled=Param("boolean", "true to start following the nearest person, false to stop following."),
)
async def follow_tool(robot: Robot, enabled: bool) -> Result:
    # A trick that walks in its own stance (the spider) cannot follow a person.
    # Follow mode needs the normal walk, so starting it would pull Pupper out of
    # the trick without anyone asking for that.
    # state_after_queue, not state_now: in "be a spider, then follow me" the
    # spider is still waiting in the queue when Gemini calls follow.
    state = robot.state_after_queue
    if enabled and isinstance(state, Trick) and state.walks:
        return Result(
            False,
            f"can't follow while in the trick {state.name}: following needs the normal walk, and "
            f"{state.name} is too slow to keep up with a person. Stand up first (stand_up), then follow.",
        )
    return await robot.set_following(enabled)
