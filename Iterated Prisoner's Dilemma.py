import random
import tkinter as tk
import itertools
import matplotlib.pyplot
import numpy as np
from pandas import DataFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import xlsxwriter as xw
from collections import OrderedDict
import sys
import statistics


class Display(tk.Tk):  # Choice to inherit from Tk instead of Frame to make things simpler

    def __init__(self, winner, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # The following code creates and displays a bar graph of agent scores
        df = new_sim.df
        figure = matplotlib.pyplot.Figure(figsize=(6, 5), dpi=100)
        ax = figure.add_subplot(111)
        chart_type = FigureCanvasTkAgg(figure, self)
        chart_type.get_tk_widget().pack()
        df = df[['Agent', 'Score']].groupby('Agent').sum()
        df.plot(kind='bar', legend=False, ax=ax)
        ax.set_title('Agent Scores')

        winner_label = tk.Label(self, text="Winner: " + str(winner))
        winner_label.pack()




class Simulation(object):
    agents = []

    def __init__(self, n_agents, n_games, n_generations):
        self.n_agents = n_agents  # The number of agents to be generated
        self.n_games = n_games  # The number of games to be played between any two agents
        self.winner = 0
        self.n_generations = n_generations
        self.generation = 0
        # Open both workbooks
        self.genome_workbook = xw.Workbook('Genome_Data.xlsx')
        self.log_workbook = xw.Workbook('Log_Data.xlsx')

        self.main()

    def main(self):
        # ------------------------------------- GAME PREP ---------------------------------------
        for ID in range(self.n_agents):
            gene_reaction_list = []
            for i in range(67):
                gene_reaction_list.append(random.choice(['C', 'D']))  # RANDOMLY GENERATED STRATEGY - 64 Reactions + 3 initial moves

            new_agent = Agent(ID, gene_reaction_list)
            self.agents.append(new_agent)

        # ------------------------------------- GAME START --------------------------------------
        for i in range(self.n_generations):
            self.createLogs()

            for j in range(self.n_games):
                self.playGame()

            scores = list(agent.score for agent in self.agents)
            self.winner = scores.index(max(scores))

            agent_data = {'Agent': [agent.ID for agent in self.agents], 'Score': [agent.score for agent in self.agents]} # Compiles data to use in graph
            self.df = DataFrame(agent_data, columns=['Agent', 'Score'])

            for i in range(5):
                try:
                    self.writeData()
                except xw.exceptions.FileCreateError:
                    input("Please close all data files open in other programs. Press ENTER to continue.")
                else:
                    break

            else:
                print("Too many failed attempts. Exiting...")
                sys.exit()

            self.generation += 1
            self.reproduce()

        # ------------------------------------- GAME END -----------------------------------------

        self.genome_workbook.close()
        self.log_workbook.close()


    def createLogs(self):
        for agent1 in self.agents:
            agent1.log = []  # DO NOT DELETE THIS LINE - I don't understand why I need it, but without it the program will break!
            for agent2 in self.agents:
                if agent1 == agent2:
                    continue
                else:
                    agent1.log.append([agent2.ID])


    def writeData(self):  # Writes all genomes to an excel file
        gene_prompt_list = Agent.generatePromptList(Agent)

        for i in range(len(gene_prompt_list)):  # Convert any tuples in gene_prompt_list to strings
            if isinstance(gene_prompt_list[i], tuple):
                gene_prompt_list[i] = ''.join(gene_prompt_list[i])
            else:
                continue

        # Two new dicts that can be properly parsed by the xlsxwriter

        genomedata = {"ID": gene_prompt_list}
        for agent in self.agents:
            genomedata[agent.ID] = list(agent.genome.values())

        logdata = {"Game": [i for i in range(self.n_games)]}
        for agent in self.agents:
            for competitor_log in agent.log:
                logdata[str(agent.ID) + " vs " + str(competitor_log[0])] = competitor_log[1:]



        # Color formats for color coded worksheet

        D_format = self.genome_workbook.add_format(properties={'bg_color': '#FF6746'})
        C_format = self.genome_workbook.add_format(properties={'bg_color': '#05D107'})

        M_format = self.log_workbook.add_format(properties={'bg_color': '#F9E30F'})
        L_format = self.log_workbook.add_format(properties={'bg_color': '#F9320F', 'font_color': '#FFFFFF'})
        S_format = self.log_workbook.add_format(properties={'bg_color': '#0FBFF9'})
        I_format = self.log_workbook.add_format(properties={'bg_color': '#000000', 'font_color': '#FFFFFF'})

        genome_worksheet = self.genome_workbook.add_worksheet(str(self.generation))
        log_worksheet = self.log_workbook.add_worksheet(str(self.generation))

        # ----------------------------GENOME WORKSHEET--------------------------------

        for row_num, header in enumerate(genomedata.keys()):
            genome_worksheet.write(0, row_num, header)

        for row_num, row_data in enumerate(zip(*genomedata.values())):
            for col_num, cell_data in enumerate(row_data):
                if cell_data == "C":
                    genome_worksheet.write(row_num + 1, col_num, cell_data, C_format)
                elif cell_data == "D":
                    genome_worksheet.write(row_num + 1, col_num, cell_data, D_format)
                else:
                    genome_worksheet.write(row_num + 1, col_num, cell_data)

        # ----------------------------LOG WORKSHEET-------------------------------------

        for row_num, header in enumerate(logdata.keys()):
            log_worksheet.write(row_num, 0, header)

        for col_num, col_data in enumerate(zip(*logdata.values())):
            for row_num, cell_data in enumerate(col_data):
                if cell_data == "M":
                    log_worksheet.write(row_num, col_num + 1, cell_data, M_format)

                elif cell_data == "L":
                    log_worksheet.write(row_num, col_num + 1, cell_data, L_format)

                elif cell_data == "W":
                    log_worksheet.write(row_num, col_num + 1, cell_data, S_format)

                elif cell_data == "F":
                    log_worksheet.write(row_num, col_num + 1, cell_data, I_format)

                else:
                    log_worksheet.write(row_num, col_num + 1, cell_data)

    def playGame(self):
        # M is CC, L is CD, W is DC, F is DD
        for agent1 in self.agents:
            for agent2 in self.agents:
                if agent1 != agent2 and agent1.ID > agent2.ID:  # Makes sure agent doesn't play itself and each agent plays each other only once
                    outcome = agent1.choice(agent2.ID) + agent2.choice(agent1.ID)
                    if outcome == "CC":
                        agent1.score += 3
                        agent2.score += 3
                        agent1.updateLog(agent2.ID, 'M')
                        agent2.updateLog(agent1.ID, 'M')
                    elif outcome == "CD":
                        agent1.score += 0
                        agent2.score += 5
                        agent1.updateLog(agent2.ID, 'L')
                        agent2.updateLog(agent1.ID, 'W')
                    elif outcome == "DC":
                        agent1.score += 5
                        agent2.score += 0
                        agent1.updateLog(agent2.ID, 'W')
                        agent2.updateLog(agent1.ID, 'L')
                    elif outcome == "DD":
                        agent1.score += 1
                        agent2.score += 1
                        agent1.updateLog(agent2.ID, 'F')
                        agent2.updateLog(agent1.ID, 'F')
                else:
                    continue

    def reproduce(self):
        # A list of the current generation of agents sorted by their score in the game that has just finished.
        ordered_agents = sorted(self.agents, key=lambda agent: agent.score, reverse=True)
        quartiles = [ordered_agents[i:i + int(self.n_agents/4)] for i in range(0, len(ordered_agents), int(self.n_agents/4))]
        new_genes = []


        # Index of each quartile. Final quartile (index 3) is not used - i.e. lower quartile of agents is removed and get no offspring.
        for position in range(int(self.n_agents/4)):
            for i in self.combineGenomes(quartiles[0][position - 1], quartiles[0][position], 2):
                new_genes.append(i)
            for j in self.combineGenomes(quartiles[1][position - 1], quartiles[1][position], 1):
                new_genes.append(j)
            for k in self.combineGenomes(quartiles[2][position - 1], quartiles[2][position], 1):
                new_genes.append(k)
        self.agents = []
        for i in range(len(new_genes)):
            new_agent = Agent(i, new_genes[i])
            self.agents.append(new_agent)

    def combineGenomes(self, agent1, agent2, n_offspring):
        offspring = []

        genes1 = random.choice([agent1.gene_reaction_list, agent2.gene_reaction_list])
        if genes1 == agent1.gene_reaction_list:
            genes2 = agent2.gene_reaction_list
        else:
            genes2 = agent1.gene_reaction_list

        # Separating the ways we deal with the 64 reaction genes and the 3 starting genes since the memory of each agent is of the past 3 moves.
        # split_genes1 = [genes1[3:19], genes1[19:35], genes1[35:51], genes1[51:67]]  # Split the gene reactions into four (arbitrary) chunks
        # split_genes2 = [genes2[3:19], genes2[19:35], genes2[35:51], genes2[51:67]]
        # PROBLEM - quarters of genomes never change unless through mutation.
        # To eliminate - Mix genes one at a time randomly between two parents. Analogous to making random cuts.

        if n_offspring >= 1:
            # offspring_split_genes1 = split_genes1[0]+split_genes2[1]+split_genes1[2]+split_genes2[3]  # Selecting bits of each parent genome to use (alternating quadrants)
            # PROBLEM - if only 1 offspring it is always the same mix of genome from genes1 and genes2. Does it matter?
            # YES IT DOES - order is always stronger-weaker in reproduction.
            # To eliminate -> assign genes1 and genes2 randomly. (For now)
            offspring_split_genes1 = []
            offspring_start_genes1 = []
            for i in range(3, 67):
                offspring_split_genes1.append(random.choice([genes1[i], genes2[i]]))
            offspring_start_genes1 = random.choice([genes1[0:3], genes2[0:3]])
            offspring_start_genes1 += offspring_split_genes1
            offspring.append(offspring_start_genes1)

        if n_offspring == 2:
            offspring_split_genes2 = []
            offspring_start_genes2 = []
            for i in range(3, 67):
                offspring_split_genes2.append(random.choice([genes1[i], genes2[i]]))
            offspring_start_genes2 = random.choice([genes1[0:3], genes2[0:3]])
            # offspring_genes2 = list(itertools.chain.from_iterable(offspring_split_genes2))
            offspring_start_genes2 += offspring_split_genes2

            offspring.append(offspring_start_genes2)

        # Mutation code. Each gene has a 1/1000 chance of mutating, giving an expected minimum number of mutations of around 1 gene in every 20 total offspring.
        for i in range(len(offspring)):
            for g_index in range(len(offspring[i])):
                x = random.uniform(0, 1)
                if x < 0.001:
                    if offspring[i][g_index] == 'C':
                        offspring[i][g_index] = 'D'
                    else:
                        offspring[i][g_index] = 'C'
                else:
                    continue


        return offspring


# Each player is an instance of class Agent
class Agent(object):

    def __init__(self, ID, gene_reaction_list):
        self.ID = ID
        self.score = 0
        self.genome = {}  # List of reactions to every possible scenario
        self.log = []  # Log that can be dumped to a file in format: [[ID, outcome1, outcome2, etc.], [ID, outcome1]]
        self.gene_reaction_list = gene_reaction_list

        gene_prompt_list = self.generatePromptList()
        for element in range(len(gene_prompt_list)):
            self.genome[gene_prompt_list[element]] = self.gene_reaction_list[element]


    def generatePromptList(self):
        genes = ['M', 'L', 'W', 'F']
        gene_prompt_list = [g for g in itertools.product(genes, repeat=3)]  # 64 scenarios in length
        gene_prompt_list = ["MOVE1", "MOVE2", "MOVE3"] + gene_prompt_list  # + first 3 moves

        return gene_prompt_list

    def choice(self, ID):
        position = ID - 1
        if len(self.log[position]) == 1:
            return self.genome["MOVE1"]
        elif len(self.log[position]) == 2:
            return self.genome["MOVE2"]
        elif len(self.log[position]) == 3:
            return self.genome["MOVE3"]
        else:
            return self.genome[tuple([i for i in self.log[position][-3:]])]

    def updateLog(self, ID, outcome):
        for element in self.log:  # Checks the log to find the entry under opponent's ID and updates it
            if element[0] == ID:
                element.append(outcome)
            else:
                continue


if __name__ == "__main__":
    new_sim = Simulation(20, 50, 30)  # (Number of agents (ONLY MULTIPLES OF 4 which are greater than 4), number of games played between any two agents, number of generations of agents to play for)
    # CLARIFICATION: The agents only ever play the specified number of games against each other, but each game is accounted twice - once from the perspective of each agent.
    # Take 0 and 1. If the 0vs1 log states: LLIMSSL...etc. then the 1vs0 log will state: SSIMLLS...etc. This way each agent keeps track of the event that occurred
    # from their own perspective, allowing easier consultation of their genome when they make a decision.
    root = Display(new_sim.winner)
    root.mainloop()
