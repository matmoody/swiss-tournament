#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2

def close(cursor, connection):
    # Close cursor and connection
    cursor.close()
    connection.close()

def get_cc():
    # Get cursor and connection
    connection = connect()
    cursor = connection.cursor()

    return connection, connection.cursor()


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    connection, cursor = get_cc()
    cursor.execute("DELETE FROM Matches;")
    connection.commit()
    close(cursor, connection)


def deletePlayers():
    """Remove all the player records from the database."""
    connection, cursor = get_cc()
    cursor.execute("DELETE FROM Players;")
    connection.commit()
    close(cursor, connection)



def countPlayers():
    """Returns the number of players currently registered."""
    connection, cursor = get_cc()
    cursor.execute("SELECT COUNT(*) from Players;")
    count_players = cursor.fetchone()[0]

    close(cursor, connection)
    return count_players


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    connection, cursor = get_cc()
    cursor.execute("INSERT INTO Players (Name) VALUES(%s)", (name,))
    connection.commit()
    close(cursor, connection)


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    query = """SELECT Win.PlayerID, Win.Name,
                COALESCE(Win."WinCount", 0),
                COALESCE(Mat."MatchCount", 0)
                FROM
                    (
                    SELECT Pla.PlayerID, Pla.Name,
                    COALESCE(wincount, 0) as "WinCount"
                    FROM Players Pla
                    LEFT JOIN (
                        SELECT Mat.PlayerID, COUNT(Mat.Result) as wincount
                        FROM Matches Mat
                        WHERE Mat.Result = 'Win'
                        GROUP By Mat.PlayerID
                        ) WC
                    ON Pla.PlayerID=WC.PlayerID
                    ) Win
                LEFT JOIN
                    (
                    SELECT Mat.PlayerID,
                    COALESCE(COUNT(Mat.Result), 0) as "MatchCount"
                    FROM Matches Mat
                    GROUP BY Mat.PlayerID
                    ) Mat
                ON Win.PlayerID=Mat.PlayerID
                ORDER By COALESCE(Win."WinCount", 0) Desc;"""

    connection, cursor = get_cc()
    cursor.execute(query)
    results = cursor.fetchall()
    close(cursor, connection)

    return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    connection, cursor = get_cc()
    cursor.execute("INSERT INTO Matches VALUES(%s, %s)", (winner, 'Win'))
    cursor.execute("INSERT INTO Matches VALUES(%s, %s)", (loser, 'Loss'))
    connection.commit()
    close(cursor, connection)
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    standings = playerStandings()

    pairings = []
    paired = []
    for player in standings:
        if len(paired) < 4:
            paired.append(player[0])
            paired.append(player[1])
        if len(paired) == 4:
            pairings.append(tuple(paired))
            paired = []

    return pairings


