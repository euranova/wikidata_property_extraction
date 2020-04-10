"""Header."""
import sys

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.user_agent = None


def initialize_user_agent(user_agent):
    """Init user_agent.

    Args:
        user_agent (str): Setting the value of user-agent.
            Follow the rules here:
            https://meta.wikimedia.org/wiki/User-Agent_policy

    """
    # also in local function scope.
    # no scope specifier like global is needed
    this.user_agent = user_agent
    # also the name remains free for local use
    user_agent = "Locally scoped db_name variable." \
        + "Doesn't do anything here."
