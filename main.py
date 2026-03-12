from Portfolio import Portfolio
import matplotlib.pyplot as plt

current: Portfolio = Portfolio.generateFromDirectory("example_data/", "Current")
reduced:Portfolio = current.reduce_portfolio("Reduced")

current.generate_clustermap("Current Cluster Map")
reduced.generate_clustermap("Reduced Cluster Map")


current.graph_returns(equal_weight=True)
current.graph_returns(equal_weight=False)

reduced.graph_returns(equal_weight=True)
reduced.graph_returns(equal_weight=False)

current.print_summary()
reduced.print_summary()

plt.show()
