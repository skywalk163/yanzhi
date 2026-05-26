



"""
优化版在线学习算法
使用更高效的增量学习和模型更新策略
"""

import numpy as np
import time
import pickle
import os
from typing import List, Dict, Any, Tuple, Optional
from collections import deque
from dataclasses import dataclass
import threading
import heapq


@dataclass
class Experience:
    """经验数据点，用于在线学习"""
    state: np.ndarray  # 状态特征
    action: int        # 采取的动作（分区数量）
    reward: float      # 得到的奖励（性能提升）
    next_state: Optional[np.ndarray]  # 下一状态
    timestamp: float   # 时间戳


class PrioritizedExperienceReplay:
    """优先经验回放缓冲区"""
    
    def __init__(self, capacity: int = 10000, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha  # 优先级指数
        self.beta = beta    # 重要性采样权重指数
        self.beta_increment = 0.001
        
        self.buffer = []  # 经验缓冲区
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.size = 0
        
        self.lock = threading.RLock()
    
    def add(self, experience: Experience, priority: float = None):
        """添加经验到缓冲区"""
        with self.lock:
            if priority is None:
                priority = np.max(self.priorities) if self.size > 0 else 1.0
            
            # 计算优先级
            priority = np.power(priority, self.alpha)
            
            if self.size < self.capacity:
                self.buffer.append(experience)
                self.size += 1
            else:
                self.buffer[self.position] = experience
            
            self.priorities[self.position] = priority
            self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> Tuple[List[Experience], np.ndarray, List[int]]:
        """从缓冲区采样一批经验"""
        with self.lock:
            if self.size == 0:
                return [], np.array([]), []
            
            # 计算采样概率
            priorities = self.priorities[:self.size] if self.size < self.capacity else self.priorities
            probs = priorities / priorities.sum()
            
            # 采样索引
            indices = np.random.choice(self.size, size=min(batch_size, self.size), p=probs)
            
            # 计算重要性采样权重
            weights = np.power(self.size * probs[indices], -self.beta)
            weights = weights / weights.max()
            
            # 更新beta
            self.beta = min(1.0, self.beta + self.beta_increment)
            
            # 获取经验
            experiences = [self.buffer[idx] for idx in indices]
            
            return experiences, weights, indices
    
    def update_priorities(self, indices: List[int], priorities: List[float]):
        """更新经验的优先级"""
        with self.lock:
            for idx, priority in zip(indices, priorities):
                if 0 <= idx < self.size:
                    self.priorities[idx] = np.power(priority, self.alpha)
    
    def __len__(self):
        return self.size


class AdaptiveGradientDescent:
    """自适应梯度下降优化器"""
    
    def __init__(self, learning_rate: float = 0.001, momentum: float = 0.9):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.velocity = None
        
    def update(self, gradients: np.ndarray, params: np.ndarray) -> np.ndarray:
        """更新参数"""
        if self.velocity is None:
            self.velocity = np.zeros_like(gradients)
        
        # 动量更新
        self.velocity = self.momentum * self.velocity - self.learning_rate * gradients
        
        # 参数更新
        params += self.velocity
        
        return params


class OptimizedOnlineLearner:
    """优化版在线学习器"""
    
    def __init__(self, 
                 state_dim: int,
                 action_dim: int,
                 learning_rate: float = 0.001,
                 gamma: float = 0.95,
                 memory_size: int = 10000,
                 batch_size: int = 32):
        """
        初始化优化版在线学习器
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            learning_rate: 学习率
            gamma: 折扣因子
            memory_size: 记忆容量
            batch_size: 批量大小
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.batch_size = batch_size
        
        # 经验回放缓冲区
        self.memory = PrioritizedExperienceReplay(capacity=memory_size)
        
        # 优化器
        self.optimizer = AdaptiveGradientDescent(learning_rate=learning_rate)
        
        # 模型参数（简化示例）
        self.q_network = self._initialize_q_network()
        self.target_network = self._initialize_q_network()
        self.update_target_network()
        
        # 跟踪统计
        self.training_stats = {
            'total_updates': 0,
            'avg_loss': 0.0,
            'avg_reward': 0.0,
            'exploration_rate': 0.5,
            'last_update': time.time(),
        }
        
        # epsilon-greedy探索
        self.epsilon = 0.5
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995
        
        # 学习控制
        self.learning_enabled = True
        self.update_frequency = 10  # 每10个经验更新一次
        self.target_update_frequency = 100  # 每100次更新同步目标网络
        self.experience_count = 0
        
        self.lock = threading.RLock()
    
    def _initialize_q_network(self) -> Dict[str, np.ndarray]:
        """初始化Q网络参数（简化版本）"""
        # 在实际应用中，这里会是神经网络层
        # 这里使用简化的线性模型作为示例
        return {
            'weights': np.random.randn(self.state_dim, self.action_dim) * 0.01,
            'bias': np.zeros(self.action_dim)
        }
    
    def predict_q_values(self, state: np.ndarray, network: str = 'q') -> np.ndarray:
        """预测Q值（状态-动作价值）"""
        if network == 'q':
            weights = self.q_network['weights']
            bias = self.q_network['bias']
        else:
            weights = self.target_network['weights']
            bias = self.target_network['bias']
        
        # 线性Q函数: Q(s,a) = s·W + b
        q_values = np.dot(state, weights) + bias
        
        return q_values
    
    def select_action(self, state: np.ndarray, explore: bool = True) -> int:
        """选择动作（分区数量）"""
        if explore and np.random.random() < self.epsilon:
            # 探索：随机选择动作
            return np.random.randint(0, self.action_dim)
        
        # 利用：选择最大Q值的动作
        q_values = self.predict_q_values(state)
        return np.argmax(q_values)
    
    def remember(self, 
                 state: np.ndarray, 
                 action: int, 
                 reward: float, 
                 next_state: Optional[np.ndarray] = None):
        """记住经验"""
        with self.lock:
            experience = Experience(
                state=state.copy(),
                action=action,
                reward=reward,
                next_state=next_state.copy() if next_state is not None else None,
                timestamp=time.time()
            )
            
            # 初始优先级基于TD误差
            if next_state is not None:
                current_q = self.predict_q_values(state)[action]
                next_q = np.max(self.predict_q_values(next_state, network='target'))
                td_error = abs(reward + self.gamma * next_q - current_q)
            else:
                td_error = abs(reward)
            
            self.memory.add(experience, priority=td_error + 1e-6)
            self.experience_count += 1
    
    def replay(self) -> Optional[float]:
        """从记忆中学习"""
        if len(self.memory) < self.batch_size or not self.learning_enabled:
            return None
        
        if self.experience_count % self.update_frequency != 0:
            return None
        
        # 采样一批经验
        experiences, weights, indices = self.memory.sample(self.batch_size)
        
        if not experiences:
            return None
        
        # 准备训练数据
        states = np.array([exp.state for exp in experiences])
        actions = np.array([exp.action for exp in experiences])
        rewards = np.array([exp.reward for exp in experiences])
        
        # 下一状态
        next_states = []
        has_next_state = []
        for exp in experiences:
            if exp.next_state is not None:
                next_states.append(exp.next_state)
                has_next_state.append(True)
            else:
                next_states.append(exp.state)  # 占位符
                has_next_state.append(False)
        next_states = np.array(next_states)
        
        # 计算目标Q值
        current_q = self.predict_q_values(states)
        next_q = self.predict_q_values(next_states, network='target')
        
        target_q = current_q.copy()
        batch_indices = np.arange(self.batch_size)
        
        # 对于有下一状态的经验，使用Bellman方程
        for i in range(self.batch_size):
            if has_next_state[i]:
                target_q[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])
            else:
                target_q[i, actions[i]] = rewards[i]
        
        # 计算损失（均方误差）
        q_values = self.predict_q_values(states)
        td_errors = target_q - q_values
        loss = np.mean(weights * np.square(td_errors))
        
        # 更新网络参数（简化的梯度下降）
        # 在实际应用中，这里会是反向传播
        gradient = np.dot(states.T, td_errors) / self.batch_size
        
        # 使用自适应梯度下降更新
        self.q_network['weights'] = self.optimizer.update(
            gradient, self.q_network['weights']
        )
        
        # 更新经验优先级
        new_priorities = np.abs(td_errors[np.arange(self.batch_size), actions]) + 1e-6
        self.memory.update_priorities(indices, new_priorities)
        
        # 更新统计
        self.training_stats['total_updates'] += 1
        self.training_stats['avg_loss'] = (
            0.99 * self.training_stats['avg_loss'] + 0.01 * loss
        )
        self.training_stats['avg_reward'] = (
            0.99 * self.training_stats['avg_reward'] + 0.01 * np.mean(rewards)
        )
        self.training_stats['last_update'] = time.time()
        
        # 更新目标网络
        if self.training_stats['total_updates'] % self.target_update_frequency == 0:
            self.update_target_network()
        
        # 衰减epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.training_stats['exploration_rate'] = self.epsilon
        
        return loss
    
    def update_target_network(self):
        """更新目标网络"""
        # 简单复制参数
        self.target_network['weights'] = self.q_network['weights'].copy()
        self.target_network['bias'] = self.q_network['bias'].copy()
    
    def get_optimal_action(self, state: np.ndarray) -> Tuple[int, np.ndarray]:
        """获取最优动作和Q值分布"""
        q_values = self.predict_q_values(state)
        optimal_action = np.argmax(q_values)
        
        # 计算动作置信度分布
        q_values_normalized = np.exp(q_values - np.max(q_values))
        q_values_normalized = q_values_normalized / np.sum(q_values_normalized)
        
        return optimal_action, q_values_normalized
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        return {
            'memory_size': len(self.memory),
            'total_updates': self.training_stats['total_updates'],
            'avg_loss': self.training_stats['avg_loss'],
            'avg_reward': self.training_stats['avg_reward'],
            'exploration_rate': self.training_stats['exploration_rate'],
            'epsilon': self.epsilon,
            'learning_enabled': self.learning_enabled,
            'experience_count': self.experience_count,
        }
    
    def save(self, filepath: str):
        """保存学习器状态"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'q_network': self.q_network,
                'target_network': self.target_network,
                'memory': self.memory,
                'training_stats': self.training_stats,
                'epsilon': self.epsilon,
                'experience_count': self.experience_count,
            }, f)
    
    def load(self, filepath: str) -> bool:
        """加载学习器状态"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    data = pickle.load(f)
                    self.q_network = data.get('q_network', self.q_network)
                    self.target_network = data.get('target_network', self.target_network)
                    self.memory = data.get('memory', self.memory)
                    self.training_stats = data.get('training_stats', self.training_stats)
                    self.epsilon = data.get('epsilon', self.epsilon)
                    self.experience_count = data.get('experience_count', self.experience_count)
                return True
        except Exception as e:
            print(f"加载学习器失败: {e}")
        
        return False


class CacheOptimizationRL:
    """缓存优化强化学习系统"""
    
    def __init__(self, 
                 state_dim: int = 12,
                 action_dim: int = 10,  # 分区数量范围
                 model_path: str = None):
        """
        初始化缓存优化强化学习系统
        
        Args:
            state_dim: 状态特征维度
            action_dim: 动作维度（分区数量范围）
            model_path: 模型保存路径
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.model_path = model_path or ".cache_optimization_rl.pkl"
        
        # 在线学习器
        self.learner = OptimizedOnlineLearner(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=0.002,
            gamma=0.9,
            memory_size=5000,
            batch_size=64
        )
        
        # 状态归一化
        self.state_mean = np.zeros(state_dim)
        self.state_std = np.ones(state_dim)
        self.state_count = 0
        
        # 性能跟踪
        self.performance_history = deque(maxlen=1000)
        self.reward_history = deque(maxlen=1000)
        
        # 从失败中学习
        self.failure_buffer = deque(maxlen=100)
        self.consecutive_failures = 0
        
        # 加载现有模型
        self.load()
    
    def normalize_state(self, state: np.ndarray) -> np.ndarray:
        """归一化状态"""
        if self.state_count == 0:
            return state
        
        # 在线更新统计
        self.state_count += 1
        alpha = 1.0 / self.state_count
        
        # 更新均值和标准差
        self.state_mean = (1 - alpha) * self.state_mean + alpha * state
        diff = state - self.state_mean
        self.state_std = np.sqrt((1 - alpha) * self.state_std**2 + alpha * diff**2)
        
        # 避免除零
        std_safe = np.where(self.state_std < 1e-6, 1.0, self.state_std)
        
        # 归一化
        normalized = (state - self.state_mean) / std_safe
        
        # 限制范围
        normalized = np.clip(normalized, -3, 3)
        
        return normalized
    
    def extract_state(self, metrics: Dict[str, Any]) -> np.ndarray:
        """从指标中提取状态特征"""
        # 简化版本：从指标中提取关键特征
        features = [
            metrics.get('cache_size', 0) / max(1, metrics.get('max_size', 1000)),
            metrics.get('hit_rate', 0.5),
            metrics.get('current_partitions', 4) / 16.0,  # 归一化到[0,1]
            metrics.get('imbalance_ratio', 1.0) / 5.0,    # 归一化
            metrics.get('lock_intensity', 0) * 1000,      # 放大
            metrics.get('read_intensity', 0.5),
            min(metrics.get('rebalance_count', 0) / 100.0, 1.0),
            metrics.get('load_ratio', 0.5),
            np.log1p(metrics.get('cache_size', 0)) / 10.0,
            np.sqrt(metrics.get('current_partitions', 4)) / 4.0,
            metrics.get('time_since_rebalance', 0) / 3600.0,  # 小时
            metrics.get('size_per_partition', 0) / 100.0,
        ]
        
        state = np.array(features, dtype=np.float32)
        return self.normalize_state(state)
    
    def calculate_reward(self, 
                        before_metrics: Dict[str, Any], 
                        after_metrics: Dict[str, Any]) -> float:
        """计算奖励值"""
        # 性能评分函数
        def performance_score(metrics):
            hit_rate = metrics.get('hit_rate', 0.5)
            lock_intensity = metrics.get('lock_intensity', 0)
            imbalance = metrics.get('imbalance_ratio', 1.0)
            
            # 综合评分
            score = (
                0.4 * hit_rate +                    # 命中率权重
                0.3 * max(0, 1.0 - lock_intensity * 1000) +  # 锁争用权重
                0.3 * max(0, 3.0 - imbalance) / 3.0  # 负载均衡权重
            )
            
            return score
        
        before_score = performance_score(before_metrics)
        after_score = performance_score(after_metrics)
        
        # 奖励 = 性能提升 - 调整惩罚
        performance_gain = after_score - before_score
        
        # 调整惩罚（避免频繁调整）
        partitions_changed = abs(
            after_metrics.get('current_partitions', 4) - 
            before_metrics.get('current_partitions', 4)
        )
        adjustment_penalty = 0.01 * partitions_changed
        
        # 最终奖励
        reward = performance_gain - adjustment_penalty
        
        # 记录
        self.performance_history.append((before_score, after_score))
        self.reward_history.append(reward)
        
        return reward
    
    def decide_action(self, metrics: Dict[str, Any], explore: bool = True) -> Tuple[int, float]:
        """决定动作（分区数量）"""
        # 提取状态
        state = self.extract_state(metrics)
        
        # 选择动作
        if explore:
            action = self.learner.select_action(state, explore=True)
        else:
            action, confidence = self.learner.get_optimal_action(state)
        
        # 动作映射到实际分区数量
        # 动作0-9映射到2-11个分区（简单映射）
        actual_partitions = action + 2
        
        # 使用探索时返回固定置信度
        confidence = self.learner.training_stats['exploration_rate'] if explore else 0.9
        
        return actual_partitions, confidence
    
    def learn_from_experience(self,
                             before_metrics: Dict[str, Any],
                             after_metrics: Dict[str, Any],
                             action_taken: int):
        """从经验中学习"""
        # 提取状态
        state_before = self.extract_state(before_metrics)
        state_after = self.extract_state(after_metrics)
        
        # 计算奖励
        reward = self.calculate_reward(before_metrics, after_metrics)
        
        # 动作索引（反向映射）
        action_index = max(0, min(self.action_dim - 1, action_taken - 2))
        
        # 记住经验
        self.learner.remember(state_before, action_index, reward, state_after)
        
        # 判断是否成功
        success = reward > 0
        
        # 从失败中学习
        if not success:
            self.failure_buffer.append((state_before, action_index, reward))
            self.consecutive_failures += 1
            
            # 如果连续失败，增加学习频率
            if self.consecutive_failures > 3:
                self.learner.update_frequency = 5  # 更频繁更新
        else:
            self.consecutive_failures = 0
        
        # 触发学习
        loss = self.learner.replay()
        
        return reward, loss
    
    def save(self):
        """保存模型"""
        self.learner.save(self.model_path)
    
    def load(self):
        """加载模型"""
        return self.learner.load(self.model_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计"""
        learner_stats = self.learner.get_statistics()
        
        # 性能历史统计
        perf_history = list(self.performance_history)
        if perf_history:
            before_scores, after_scores = zip(*perf_history)
            avg_gain = np.mean([a - b for b, a in zip(before_scores, after_scores)])
        else:
            avg_gain = 0.0
        
        rewards = list(self.reward_history)
        avg_reward = np.mean(rewards) if rewards else 0.0
        
        return {
            **learner_stats,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'avg_performance_gain': avg_gain,
            'avg_reward': avg_reward,
            'performance_history_size': len(self.performance_history),
            'failure_buffer_size': len(self.failure_buffer),
            'consecutive_failures': self.consecutive_failures,
            'state_normalization_samples': self.state_count,
        }


# 全局RL优化系统实例
_rl_optimizer_instance = None

def get_cache_rl_optimizer() -> CacheOptimizationRL:
    """获取全局缓存RL优化器实例"""
    global _rl_optimizer_instance
    if _rl_optimizer_instance is None:
        _rl_optimizer_instance = CacheOptimizationRL()
    return _rl_optimizer_instance


if __name__ == '__main__':
    # 测试RL优化器
    rl_optimizer = CacheOptimizationRL()
    print("缓存优化强化学习系统初始化完成")
    
    # 测试状态提取
    test_metrics = {
        'cache_size': 150,
        'max_size': 1000,
        'hit_rate': 0.75,
        'current_partitions': 4,
        'imbalance_ratio': 1.5,
        'lock_intensity': 0.002,
        'read_intensity': 0.8,
        'rebalance_count': 10,
        'load_ratio': 0.15,
        'time_since_rebalance': 1800,
        'size_per_partition': 37.5,
    }
    
    state = rl_optimizer.extract_state(test_metrics)
    print(f"状态向量: {state[:4]}... (维度: {len(state)})")
    
    # 测试决策
    actions, confidence = rl_optimizer.decide_action(test_metrics, explore=True)
    print(f"建议动作: {actions} 分区 (置信度: {confidence:.2f})")
    
    # 获取统计
    stats = rl_optimizer.get_statistics()
    print(f"系统统计: {stats}")


