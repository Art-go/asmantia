# Asmantia
This is a dnd inspired game, or rather, a tool for me to use during my sessions.
Originally, i wanted to make it into an online game, so players could connect to server and control their characters,
but after thinking about it: this is a bit of a big goal, so now i am focusing on porting everything from unity.

Also, it uses my own abstraction layer on top of pygame, which i might turn into a full lib


<details>
<summary>Old Description</summary>

# Asmantia
This is a simple project of mine, a dnd inspired game, or rather: a client and server part of it

It is very simple to use:

## Client:
1. Run setup script
2. Launch `client.py`
3. Enter ip, port and creds given to you by me or someone else

## Server:
1. Run setup script
2. Create `Data/credentials.json` and fill it like this:
   ```json
   {
     "PLAYER_NAME+SALT": {"sheet":  "ID_OF_SHEET"}
   }
   ```
   For salt generation I used duckduckgo with query "pw 8 average"
   
   ID of sheet can be found in the sheet itself, which are located at `Data/Char Sheets`
   
   To give yourself admin rights, add `"root": true` to your credentials entry
3. Edit `server.cfg.json`
4. Launch server.py


## Requirements
- Python 3.12+


</details>