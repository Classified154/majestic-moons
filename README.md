# Majestic Moons

### **Project Description**
This game consists of a 3x3 river grid with 8 rafts and 1 empty space. The rafts have numbered stones on them, with the stones numbered in pairs and evenly distributed over the rafts. At the start of the game, the board is shown for a short time before the numbers are hidden. The goal is to find matching numbered stones. Each turn, one of the rafts adjacent to the empty space moves into it, taking the stones with it to new positions.

This is a game all about information, remember it and save the rafts from sinking by finding the matching numbered stones and throwing into the river!

### **Usage**
To setup the bot, make a `.env` file and put `BOT_TOKEN=<your_token>` in it and replace the id in [test_guilds](https://github.com/Classified154/majestic-moons/blob/main/bot/bot.py#L77) with your servers id. To start the bot, run the `bot.py` file.

The command to start a game is `/game`, it has three difficulty settings; easy, medium and hard with the rafts carrying 3, 4 and 5 numbered stones respectively.

Initially the board is shown to the player for some time to look at it and remember the positions of the stones.  
![image](https://github.com/user-attachments/assets/131a5f83-9073-4d3d-b4fd-493639315a0c)

Next, the player has to select a pair using the dropdown menu.  
![image](https://github.com/user-attachments/assets/24f2d2ba-a71e-49ac-b4af-4a18625c2515)

After selecting the pair, the player is shown the numbers on the stones they selected and whether they match or not.  
![image](https://github.com/user-attachments/assets/e9b5fa50-7f5f-4662-abb9-460407bf7f2d)

Then one of the rafts adjacent to the empty space is shifted in it.  
![image](https://github.com/user-attachments/assets/5bf9ed1a-0281-412e-9fa3-dbc16a2365b0)

And then it repeats and the player has to find pairs until they win.  
Win image? Well... win a game and see it yourself!

***INFO: Rafts and stones numbering.***  
Rafts:  
![image](https://github.com/user-attachments/assets/5420d099-2fab-4c2a-9522-64bef558a282)

Rocks:  
![image](https://github.com/user-attachments/assets/15c201f5-c306-4efd-a4fd-6c6f7ce5f510)
![image](https://github.com/user-attachments/assets/f169ff2e-de3e-4012-9aad-cb7fbbe70e19)
![image](https://github.com/user-attachments/assets/201ad6b4-9acb-4105-aeba-93fc9d4b3d58)





### **Theme relevancy**
When a game starts, the player is dumped with the information on the position of the numbers which they have to remember to eventually find the pairs, so an initial information dump, which gradually increases as the game progresses because after every turn, a raft moves, hence the player has to keep track of the position of the numbers. Combining both, we get "Information Overload", this year's [code jam](https://www.pythondiscord.com/events/code-jams/11) theme.

### **Contributions**
[`classified154`](https://github.com/Classified154): game logic, bug fixes and overall bot completion  
[`g00d__man`](https://github.com/Sai-Prabhav): raft movement and game logic  
[`aroson.`](https://github.com/Aroson1): board art and generation  
[`sibi0001`](https://github.com/Sibi-Agilan-17): commands completion  
[`astar777`](https://github.com/Astar-777): initial idea, some minor fixes and documentation
