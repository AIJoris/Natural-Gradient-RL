from Gauss import Gauss
import numpy as np
from matplotlib import pyplot as plt
from helper import Helper
from torch import nn
import torch
import torch.nn.functional as F
plt.rcParams.update({'font.size': 18})

helper = Helper()


param = 'exp'
episodes = 2000

NUMBER_OF_RUNS = 50


if param == 'exp':
	alpha_van = 0.05
	alpha_nat = 0.2

if param == "sigma":
	alpha_van = 0.15
	alpha_nat = 0.15
smooth = 20

# alpha voor exp was 0.2 en 0.05 voor allebei

def sigma_param(sigma):
	if param == 'exp':
		return np.exp(sigma)
	if param == 'sigma':
		return sigma**2

def derivative_sigma_param(sigma, mean, action, fisher_mean_sum, fisher_sigma_sum, fisher_N, fisher=False):
	if param == 'exp':
		mean_grad = (action - mean) / np.exp(sigma)**2
		sigma_grad = -1 + ((action - mean)**2 / np.exp(sigma)**2)
		if fisher:
			fisher_N += 1
			fisher_mean_sum += 1/np.exp(sigma)**2 
			fisher_mean_mean = fisher_mean_sum / fisher_N
			fisher_mean_inverse = 1/fisher_mean_mean
			fisher_sigma_sum = fisher_sigma_sum
			fisher_sigma_inverse = 1/2
			return mean_grad * fisher_mean_inverse, sigma_grad * fisher_sigma_inverse,  fisher_mean_sum, fisher_sigma_sum, fisher_N
		return mean_grad, sigma_grad
	if param == 'sigma':
		mean_grad = (action - mean)/(sigma**4)
		sigma_grad = (-2/sigma) + ((action - mean)**2 * 2 * sigma)/(sigma_param(sigma)**3)
		if fisher:
			fisher_N += 1
			fisher_mean_sum += 1/sigma_param(sigma)**2
			fisher_mean_mean = fisher_mean_sum / fisher_N
			fisher_mean_inverse = 1/fisher_mean_mean

			fisher_sigma_sum +=  8/sigma_param(sigma)
			fisher_sigma_mean = fisher_sigma_sum/fisher_N
			fisher_sigma_inverse = 1/fisher_sigma_mean
			return mean_grad * fisher_mean_inverse, sigma_grad * fisher_sigma_inverse, fisher_mean_sum, fisher_sigma_sum, fisher_N
		return mean_grad, sigma_grad


def rewardfunction(distribution):
	normal = torch.distributions.Normal(4, 2)
	reward = np.exp(normal.log_prob(action)).numpy()
	return reward


results = []
learning_rates = [0.05, 0.15, 0.45]
for learning_rate in learning_rates:
	SGD_results = np.zeros((NUMBER_OF_RUNS, episodes))
	NG_results = np.zeros((NUMBER_OF_RUNS, episodes))
	for t in range(NUMBER_OF_RUNS):
		model = Gauss() 
		print(model.mean, model.std, "INITALISIATION")
		returns= []
		losses = []
		fisher_mean_sum = 0
		fisher_sigma_sum = 0
		fisher_N = 0 
		for i in range(episodes):
			action, log_action = model.forward(sigma_param)
			G = rewardfunction(action)
			returns.append(G)

			grad_mean, grad_sigma = derivative_sigma_param(model.std, model.mean, action, fisher_mean_sum, fisher_sigma_sum, fisher_N, fisher=False)
			
			if param == "sigma":
				model.std =  np.clip(model.std + learning_rate * grad_sigma * G, 1, -1)
			else:
				model.std =  model.std + learning_rate * grad_sigma * G
			model.mean = model.mean + learning_rate * grad_mean * G

			loss = -G * log_action
			losses.append(loss)
		print(model.mean, model.std)

		SGD_results[t] = returns


		returns_NG = []
		model = Gauss()
		fisher_mean_sum = 0
		fisher_sigma_sum = 0
		fisher_N = 0 
		for i in range(episodes):
			action, log_action = model.forward(sigma_param)
			G = rewardfunction(action)
			returns_NG.append(G)
			grad_mean, grad_sigma, fisher_mean_sum, fisher_sigma_sum, fisher_N = derivative_sigma_param(model.std, model.mean, action, fisher_mean_sum, fisher_sigma_sum, fisher_N, fisher=True)
			if param == "sigma":
				model.std =  np.clip(model.std + learning_rate * grad_sigma * G, 1, -1)
			else:
				model.std =  model.std + learning_rate * grad_sigma * G
			model.mean = model.mean + learning_rate * grad_mean * G
			loss = - G * log_action

		NG_results[t] = returns_NG

	# Calculating average per episode
	average_return_SGD = helper.smooth(np.mean(SGD_results, axis=0), smooth)
	average_return_NG = helper.smooth(np.mean(NG_results, axis=0), smooth)
	results.append(average_return_NG)
	results.append(average_return_SGD)

counter = 0
for i, result in enumerate(results):
	if counter == 2:
		linestyle = ":"
	elif counter == 0:
		linestyle = "-"
	else:
		linestyle = (0, (5, 10))
	if i % 2 == 0:
		print(linestyle)
		plt.plot(result, linestyle=linestyle, color="red",  label='Natural SGD Learning rate: ' + str(learning_rates[counter]))
	else:
		plt.plot(result, linestyle=linestyle, color="blue", label='Vanilla SGD Learning rate: ' + str(learning_rates[counter]))
		counter += 1


if param == "exp":
	text = r'$\sigma(\theta) = \exp(\theta)$'
else:
	text = r'$\sigma(\theta) = \theta^2$'

plt.xlabel("Episodes")
plt.ylabel("Average return")
plt.title("Average return per episode for parametrization " + text + " \n with different learning rates (50 runs)")
plt.legend(loc = 4, fontsize=10)
plt.show()


# plt.plot(helper.smooth(returns, 10))
# plt.show()

# plt.plot(helper.smooth(losses, 10))
# plt.show()



