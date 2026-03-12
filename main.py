from Portfolio import Portfolio
import matplotlib.pyplot as plt

current: Portfolio = Portfolio.generateFromDirectory("data/", "Current")
reduced:Portfolio = current.reduce_portfolio("Reduced")

current.generate_clustermap("Current Cluster Map")
reduced.generate_clustermap("Reduced Cluster Map")

reduced.graph_returns(True)
reduced.graph_returns(False)

reduced.print_summary()

plt.show()
