import csv
import random

team1_battingorder = []
team1_bowlingorder = []
team2_battingorder = []
team2_bowlingorder = []
tname = []

lookup_table = [0, 1, 2, 3, 4, 6, 7] # Here 7 means the batsman got out, this is for reference to the probability table.

#This code takes input from csv files
with open('input/MIvsDD.csv', 'rb') as f:
    match_reader = csv.reader(f)
    match_reader.next()
    for row in match_reader:
        tname.append(row[0])
        team1_battingorder.append(row[1])
        team1_bowlingorder.append(row[2])
        team2_battingorder.append(row[3])
        team2_bowlingorder.append(row[4])

    	
team1_battingorder = [x for x in team1_battingorder if x != '']
team1_bowlingorder = [x for x in team1_bowlingorder if x != '']
team2_battingorder = [x for x in team2_battingorder if x != '']
team2_bowlingorder = [x for x in team2_bowlingorder if x != '']
#Since there are only 20 overs, we need only 5 bowlers from each team to bowl 4 overs each.
team1_bowlingorder = team1_bowlingorder[:5] 
team2_bowlingorder = team2_bowlingorder[:5]


def cluster_number(batsman, bowler) :

	#Batsman's cluster number
	with open('data/Batting_Clusters.csv', 'rb') as f:
	    bat_cluster_reader = csv.reader(f)
	    for row in bat_cluster_reader:
	    	if batsman == row[0]:
	    		curr_bat_cluster_num = row[4]


	#Bowler's cluster number
	with open('data/Bowling_Clusters.csv', 'rb') as f:
	    bow_cluster_reader = csv.reader(f)
	    for row in bow_cluster_reader:
	    	if bowler == row[0]:
	    		curr_bow_cluster_num = row[4]

	return curr_bat_cluster_num, curr_bow_cluster_num


# Function to get the row from the PvP csv file.
def pvp_plist(batsman, bowler) :
	global probability_list
	pvp_check = False
	with open('data/PvP.csv', 'rb') as f:
	    pvp_reader = csv.reader(f)
	    for row in pvp_reader:
	    	if batsman == row[0] and bowler == row[1]:
	    		pvp_check = True
	    		probability_list = row
	    		"""
	    		probability_list 
	    		0,       1,	     2,  3,  4,  5,  6,  7,  8			9
				Batsman, Bowler, 0s, 1s, 2s, 3s, 4s, 6s, Dismissal, BallsFaced
				"""
                break
				
	if pvp_check :		
		probability_list = map(float, probability_list)
		probability_list = probability_list[2:9]
		return pvp_check,probability_list #Returned if there exists a valid row.
	else :
		return pvp_check,None
	
#A function to return corresponding row from Cluster v Cluster Probabilites 
def gvg_plist(bat_cluster_number, bowler_cluster_number) :
	global probability_list
	with open('data/GvG.csv', 'rb') as f:
	    gvg_reader = csv.reader(f)
	    for row in gvg_reader:
	    	if bat_cluster_number == row[0] and bowler_cluster_number == row[1]:
	    		probability_list = row
	    		"""
	    		probability_list 
	    		0,              1,	           2,  3,  4,  5,  6,  7,  8
				BatsmanCluster, BowlerCluster, 0s, 1s, 2s, 3s, 4s, 6s, Dismissal
				"""
	probability_list = map(float, probability_list)
	probability_list = probability_list[2:]
	return probability_list

def get_balls_faced(batsman, bowler) :
	ball_number = 0
	with open('data/PlayerVsPlayer1.csv', 'rb') as f:
	    pvp_reader = csv.reader(f)
	    for row in pvp_reader:
	    	if batsman == row[0] and bowler == row[1]:
	    		ball_number = int(row[2])
                break
	return ball_number

#This function predicts what the outcome of the current ball will be.
def pick_outcome(some_list,curr_bats,curr_bowl) :
	global item
	ball_number=0
	flag,pvp_p_list = pvp_plist(curr_bats,curr_bowl)
	if flag:
		ball_number=get_balls_faced(curr_bats,curr_bowl)
	bat_c_num, bow_c_num = cluster_number(curr_bats, curr_bowl)
	gvg_p_list = gvg_plist(bat_c_num, bow_c_num)
	event=-1
	if flag:
		x = random.uniform(0,max(sum(pvp_p_list),sum(gvg_p_list)))
		cp1=0.0
		cp2=0.0
		cumulative_prob = 0.0
		if ball_number >= 6 and ball_number <=10:
			for item,ip1,ip2 in zip(some_list,pvp_p_list,gvg_p_list):
				cp1 += ip1
				cp2 += ip2
				cumulative_prob = 0.5*cp1 +0.5*cp2
				if x < cumulative_prob: break
			event=item
		elif ball_number < 6:
			for item,ip1,ip2 in zip(some_list,pvp_p_list,gvg_p_list):
				cp1 += ip1
				cp2 += ip2
				cumulative_prob = 0.2*cp1 +0.8*cp2
				if x < cumulative_prob: break
			event=item
		else:
			for item,ip1,ip2 in zip(some_list,pvp_p_list,gvg_p_list):
				cp1 += ip1
				cp2 += ip2
				cumulative_prob = 0.7*cp1 +0.3*cp2
				if x < cumulative_prob: break
			event=item
	else:
		x = random.uniform(0,sum(gvg_p_list))
		cumulative_probability = 0.0
		for item, item_probability in zip(some_list, gvg_p_list):
			cumulative_probability += item_probability
			if x < cumulative_probability: break
		event=item
	return event


#This is the function that simulates the match for each team.
def innings(bat_order, bow_order, inn) : 
	global first_inn_score
	tot_wickets = 0
	m = 1    #Strike batsman
	n = 0  #Non-strike batsman
	bow_index_order = [0,1,0,1,2,3,4,2,3,4,2,3,4,2,3,4,0,1,0,1]#Pre-determined bowling order of both teams.(for simplicity :D)  
	x = bow_index_order[0]

	total_runs = 0
	k = -1

	for i in range(0,120) :

		# Swap batsmen and Change bowlers for every 6 balls
		if i%6 == 0 :
			k += 1
			x = bow_index_order[k]

			tmp_m = m
			m = n
			n = tmp_m

		curr_bat = bat_order[m]
		other_bat = bat_order[n]
		curr_bow = bow_order[x]

		prediction = pick_outcome(lookup_table, curr_bat,curr_bow)

		# If prediction is a dot ball, 2, 4 or 6, the strike batsman doesnt change. 
		if prediction==0 or prediction==2 or prediction==4 or prediction==6: 
			total_runs+=prediction
			print("(Over:"+str(k)+" Ball:"+str((i%6)+1)+") "+curr_bat+" hits the ball for "+str(prediction)+" off "+curr_bow+". Score:"+str(total_runs)+"/"+str(tot_wickets)+"\n") 

		# If prediction is 1 or 3, strike and non-strike interchange positions.
		elif prediction==1 or prediction==3:
			total_runs+=prediction
			print("(Over:"+str(k)+" Ball:"+str((i%6)+1)+") "+curr_bat+" hits the ball for "+str(prediction)+" off "+curr_bow+". Score:"+str(total_runs)+"/"+str(tot_wickets)+"\n") 
			tmp_m = m
			m = n
			n = tmp_m
			
		# If prediction is an out, since only the strike batsman can get out, we get the next batsman to the strike position.
		else:
			tot_wickets+=1
			print("(Over:"+str(k)+" Ball:"+str((i%6)+1)+") "+curr_bow+" got a wicket! "+curr_bat+" has to depart. Score:"+str(total_runs)+"/"+str(tot_wickets)+"\n") 
			m=max(m,n) + 1

			# If they are all out
			if m > 10 :
				print("(Over:"+str(k)+" Ball:"+str((i%6)+1)+") All Out! Score:"+str(total_runs)+"/"+str(tot_wickets)+"\n") 
				break
		
		# If it is second innings and if the team has chased the target
		if inn == 2 and total_runs > first_inn_score :
			break
			

	if inn == 1 :

		first_inn_score = total_runs
				
	num_of_overs_played = str(int((i+1)/6)) + "." + str((i+1)%6)  
	return total_runs, str(total_runs)+"/"+str(tot_wickets)+" Overs : "+ num_of_overs_played



print "\n----------------------------------------------------------------------------------------------------------\n"
print "                             IPL Match Prediction                                                           "
print "\n----------------------------------------------------------------------------------------------------------\n"

print tname[0] + " Vs. " + tname[1] + "\n"
print "----------------------------------------------------------------------------------------------------------\n"
print tname[0] + " Batting first\n"
print "----------------------------------------------------------------------------------------------------------\n"
first_innings_score, formatted_score1 = innings(team1_battingorder, team2_bowlingorder, 1)
print "\n" +tname[0]+ " Score : " + formatted_score1 + "\n--------------------------------------------------------------------------------------\n"
print tname[1] + " Chasing\n"

second_innings_score, formatted_score2 = innings(team2_battingorder, team1_bowlingorder, 2)
print "\n" +tname[1]+ " Score : " + formatted_score2 + "\n--------------------------------------------------------------------------------------\n"

if first_innings_score > second_innings_score :
	print tname[0] + " wins!"
elif second_innings_score > first_innings_score :
	print tname[1] + " wins!"
else :
	print "Match Tied."

