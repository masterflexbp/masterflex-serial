"""Asynchronous command line utility."""
import asyncio
import re
import sys


def get_params(cmd):
    """Decode parameters.

    :param cmd:
    :return:
    """
    # Get the text between quote first
    quoted = re.compile('"[^"]*"')

    # Get all the sentence between quote " "
    cmd_list = quoted.findall(cmd)

    quote_dict = {}

    # Replace the original text by -. For example "Chip Kelly" -> "Chip-Kelley"
    for q in cmd_list:
        q1 = q.replace(" ", "-")
        cmd = cmd.replace(q, q1)

        # Keep a record here to replace later - but remove the quote "
        # -> become string instead of class
        quote_dict[q1.replace('"', '')] = q.replace('"', '')

    # Remove the " signed before split the text
    cmd = cmd.replace('"', '')

    # The first command: ' '.join(cmd.split()) will remove the double space first
    # ls   hello => ls hello
    # The second part of the command .split(' ') to split the string by space
    # ls hello => ['ls', 'hello']
    all_commands = ' '.join(cmd.split()).split(' ')

    all_cmds = []
    for cm in all_commands:

        # Replace to the original string with " " space instead of "-"
        if cm in quote_dict.keys():
            print(quote_dict[cm])
            all_cmds.append(quote_dict[cm])
        else:
            all_cmds.append(cm)

    return all_cmds


async def ainput() -> str:
    """Asynchronous input."""
    # await asyncio.get_event_loop().run_in_executor(
    #        None, lambda s=string: sys.stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
        None, sys.stdin.readline)
