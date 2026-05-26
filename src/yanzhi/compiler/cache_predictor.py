


"""
基于机器学习的缓存分区预测器
使用历史数据预测最优分区数量
"""

import numpy as np
import json
import pickle
import os
import time
from typing import List, Dict, Any, Tuple, Optional
from collections import deque
from dataclasses import dataclass, asdict


@dataclass
class CacheMetrics:
    """缓存指标数据点"""
    timestamp: float
    cache_size: int
    max_size: int
    current_partitions: int
    min_partitions: int
    max_partitions: int
    partition_sizes: List[int]
    hit_rate: float
    read_write_ratio: float
    total_lock_wait_time: float
    total_lock_wait_count: int
    rebalance_count: int
    performance_score: float = 0.0


@dataclass
class PartitionPrediction:
    """分区预测结果"""
    optimal_partitions: int
    confidence: float
    predicted_performance_gain: float
    reason: str
    features: Dict[str, float]
    timestamp: float


class CachePredictor:
    """
    缓存分区预测器
    基于历史数据使用机器学习方法预测最佳分区数量
    """
    
    def __init__(self, 
                 history_size: int = 1000,
                 model_path: str = None):
        """
        初始化预测器
        
        Args:
            history_size: 历史数据最大存储量
            model_path: 模型保存路径（可选）
        """
        self.history = deque(maxlen=history_size)
        self.predictions = deque(maxlen=100)
        self.model_path = model_path or ".cache_predictor_model.pkl"
        self.model = None
        self.feature_scaler = None
        self.last_training_time = 0
        self.training_interval = 3600  # 每1小时重新训练
        
    def add_metrics(self, metrics: CacheMetrics):
        """添加新的性能指标"""
        self.history.append(metrics)
        
        # 自动训练
        if (time.time() - self.last_training_time > self.training_interval and
            len(self.history) > 50):
            self.train_model()
    
    def extract_features(self, metrics: CacheMetrics) -> Dict[str, float]:
        """从指标中提取特征"""
        partition_sizes = metrics.partition_sizes
        if not partition_sizes:
            partition_sizes = [0]
        
        # 计算不均衡比例
        avg_size = sum(partition_sizes) / len(partition_sizes)
        max_size = max(partition_sizes) if partition_sizes else 0
        imbalance_ratio = max_size / avg_size if avg_size > 0 else 1.0
        
        # 锁争用强度
        lock_intensity = (metrics.total_lock_wait_time / 
                         max(1, metrics.total_lock_wait_count))
        
        # 负载特征
        load_ratio = metrics.cache_size / max(1, metrics.max_size)
        
        # 访问模式特征
        read_intensity = min(metrics.read_write_ratio, 10.0) / 10.0
        
        features = {
            # 基础特征
            'cache_size': float(metrics.cache_size),
            'load_ratio': load_ratio,
            'current_partitions': float(metrics.current_partitions),
            
            # 性能特征
            'hit_rate': metrics.hit_rate,
            'imbalance_ratio': imbalance_ratio,
            'lock_intensity': lock_intensity,
            'read_intensity': read_intensity,
            
            # 派生特征
            'size_per_partition': float(metrics.cache_size) / max(1, metrics.current_partitions),
            'log_cache_size': np.log1p(float(metrics.cache_size)),
            'sqrt_partitions': np.sqrt(float(metrics.current_partitions)),
            
            # 时间特征（归一化到0-1）
            'time_since_rebalance': min(metrics.rebalance_count, 100) / 100.0,
        }
        
        return features
    
    def calculate_performance_score(self, metrics: CacheMetrics) -> float:
        """计算性能评分（用于训练标签）"""
        partition_sizes = metrics.partition_sizes
        if not partition_sizes:
            return 0.5
        
        # 1. 命中率权重 (40%)
        hit_rate_score = metrics.hit_rate * 0.4
        
        # 2. 锁争用权重 (30%)
        avg_lock_wait = (metrics.total_lock_wait_time / 
                        max(1, metrics.total_lock_wait_count))
        lock_score = max(0, 1.0 - min(avg_lock_wait * 1000, 1.0)) * 0.3
        
        # 3. 负载均衡权重 (20%)
        avg_size = sum(partition_sizes) / len(partition_sizes)
        if avg_size > 0:
            imbalance = max(partition_sizes) / avg_size
            balance_score = max(0, 2.0 - imbalance) * 0.2
        else:
            balance_score = 0.2
        
        # 4. 分区效率权重 (10%)
        ideal_partitions = int(np.sqrt(metrics.cache_size)) + 1
        partitions_diff = abs(metrics.current_partitions - ideal_partitions)
        efficiency_score = max(0, 1.0 - partitions_diff / 10.0) * 0.1
        
        total_score = hit_rate_score + lock_score + balance_score + efficiency_score
        return min(1.0, total_score)
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[CacheMetrics]]:
        """准备训练数据"""
        if len(self.history) < 10:
            return np.array([]), np.array([]), []
        
        X = []
        y = []
        selected_metrics = []
        
        # 选择最近的数据点，同时确保多样性
        recent_metrics = list(self.history)[-min(100, len(self.history)):]
        
        for metrics in recent_metrics:
            # 计算性能评分作为标签
            score = self.calculate_performance_score(metrics)
            metrics.performance_score = score
            
            # 提取特征
            features = self.extract_features(metrics)
            feature_vector = list(features.values())
            
            # 目标：最优分区数量（离散化）
            # 我们将性能评分作为连续标签，在预测时再转换为分区数量
            X.append(feature_vector)
            y.append(score)
            selected_metrics.append(metrics)
        
        return np.array(X), np.array(y), selected_metrics
    
    def train_model(self):
        """训练预测模型"""
        X, y, metrics_list = self.prepare_training_data()
        
        if len(X) < 10:
            return False  # 数据不足
        
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 标准化特征
            self.feature_scaler = StandardScaler()
            X_train_scaled = self.feature_scaler.fit_transform(X_train)
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # 训练随机森林回归模型
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # 评估模型
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            print(f"[CachePredictor] 模型训练完成")
            print(f"  训练集 R²: {train_score:.3f}")
            print(f"  测试集 R²: {test_score:.3f}")
            print(f"  数据点: {len(X)}")
            
            self.last_training_time = time.time()
            
            # 保存模型
            self.save_model()
            
            return True
            
        except ImportError:
            # sklearn不可用，使用简单启发式方法
            print("[CachePredictor] scikit-learn不可用，使用启发式预测")
            return self.train_heuristic_model()
    
    def train_heuristic_model(self):
        """训练启发式模型（当scikit-learn不可用时）"""
        # 简单启发式：基于历史最佳实践
        self.model = "heuristic"
        self.last_training_time = time.time()
        return True
    
    def predict_optimal_partitions(self, 
                                  current_metrics: CacheMetrics,
                                  min_partitions: int = 2,
                                  max_partitions: int = 16) -> PartitionPrediction:
        """预测最优分区数量"""
        
        # 提取特征
        features = self.extract_features(current_metrics)
        feature_vector = np.array([list(features.values())])
        
        if self.model is None:
            # 如果没有训练好的模型，使用启发式方法
            return self.heuristic_prediction(current_metrics, min_partitions, max_partitions)
        
        if self.model == "heuristic":
            # 使用启发式模型
            return self.heuristic_prediction(current_metrics, min_partitions, max_partitions)
        
        try:
            # 标准化特征
            if self.feature_scaler is not None:
                feature_scaled = self.feature_scaler.transform(feature_vector)
            else:
                feature_scaled = feature_vector
            
            # 预测性能评分
            predicted_score = self.model.predict(feature_scaled)[0]
            
            # 将性能评分转换为分区数量
            # 我们搜索一个范围内的分区数量，选择预测性能最好的
            candidate_partitions = list(range(min_partitions, max_partitions + 1, 2))
            best_partitions = current_metrics.current_partitions
            best_score = predicted_score
            confidence = 0.7  # 默认置信度
            
            # 简单启发式：根据缓存大小调整
            ideal_by_size = int(np.sqrt(current_metrics.cache_size)) + 1
            ideal_by_size = max(min_partitions, min(max_partitions, ideal_by_size))
            
            # 结合两种方法
            if current_metrics.cache_size > 100:
                # 大缓存：优先考虑性能预测
                if predicted_score < 0.6:
                    optimal_partitions = max(min_partitions, 
                                           current_metrics.current_partitions + 2)
                elif predicted_score > 0.8:
                    optimal_partitions = min(max_partitions,
                                           current_metrics.current_partitions - 1)
                else:
                    optimal_partitions = ideal_by_size
            else:
                # 小缓存：使用基于大小的启发式
                optimal_partitions = ideal_by_size
            
            # 确保在范围内
            optimal_partitions = max(min_partitions, min(max_partitions, optimal_partitions))
            
            # 计算预测性能增益（估计）
            current_score = self.calculate_performance_score(current_metrics)
            predicted_gain = max(0, predicted_score - current_score)
            
            # 生成预测原因
            reason = self.generate_prediction_reason(
                current_metrics, optimal_partitions, predicted_gain, features
            )
            
            prediction = PartitionPrediction(
                optimal_partitions=optimal_partitions,
                confidence=confidence,
                predicted_performance_gain=predicted_gain,
                reason=reason,
                features=features,
                timestamp=time.time()
            )
            
            self.predictions.append(prediction)
            return prediction
            
        except Exception as e:
            print(f"[CachePredictor] 预测失败: {e}")
            # 回退到启发式方法
            return self.heuristic_prediction(current_metrics, min_partitions, max_partitions)
    
    def heuristic_prediction(self, 
                            metrics: CacheMetrics,
                            min_partitions: int,
                            max_partitions: int) -> PartitionPrediction:
        """启发式预测（当机器学习模型不可用时）"""
        
        cache_size = metrics.cache_size
        current_partitions = metrics.current_partitions
        
        # 基于缓存大小的简单启发式
        if cache_size < 50:
            optimal = max(min_partitions, 2)
            reason = "小缓存，使用最小分区减少开销"
        elif cache_size < 200:
            optimal = max(min_partitions, 4)
            reason = "中等缓存，适中分区平衡性能"
        elif cache_size < 1000:
            optimal = max(min_partitions, 8)
            reason = "大缓存，较多分区减少争用"
        else:
            optimal = min(max_partitions, 16)
            reason = "超大缓存，最大分区支持高并发"
        
        # 考虑锁争用
        avg_lock_wait = (metrics.total_lock_wait_time / 
                        max(1, metrics.total_lock_wait_count))
        if avg_lock_wait > 0.001:  # 1毫秒
            optimal = min(max_partitions, optimal + 2)
            reason += " (检测到锁争用，增加分区)"
        
        # 考虑负载均衡
        if metrics.partition_sizes:
            avg_size = sum(metrics.partition_sizes) / len(metrics.partition_sizes)
            if avg_size > 0:
                max_size = max(metrics.partition_sizes)
                if max_size / avg_size > 2.0:
                    optimal = min(max_partitions, optimal + 1)
                    reason += " (检测到负载不均衡，增加分区)"
        
        # 确保在范围内
        optimal = max(min_partitions, min(max_partitions, optimal))
        
        prediction = PartitionPrediction(
            optimal_partitions=optimal,
            confidence=0.6,  # 启发式方法置信度较低
            predicted_performance_gain=0.1,  # 估计增益
            reason=reason,
            features=self.extract_features(metrics),
            timestamp=time.time()
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def generate_prediction_reason(self,
                                  metrics: CacheMetrics,
                                  optimal_partitions: int,
                                  predicted_gain: float,
                                  features: Dict[str, float]) -> str:
        """生成预测原因解释"""
        reasons = []
        
        if optimal_partitions > metrics.current_partitions:
            reasons.append(f"建议增加分区到 {optimal_partitions}")
            
            if features.get('imbalance_ratio', 1.0) > 1.5:
                reasons.append("检测到负载不均衡")
            
            if features.get('lock_intensity', 0) > 0.0005:
                reasons.append("锁争用较高")
                
            if features.get('cache_size', 0) > 200:
                reasons.append("缓存规模较大")
                
        elif optimal_partitions < metrics.current_partitions:
            reasons.append(f"建议减少分区到 {optimal_partitions}")
            
            if features.get('size_per_partition', 0) < 20:
                reasons.append("每个分区负载较轻")
            
            if features.get('cache_size', 0) < 100:
                reasons.append("缓存规模较小")
                
        else:
            reasons.append(f"保持当前 {optimal_partitions} 分区")
            reasons.append("当前配置表现良好")
        
        if predicted_gain > 0.05:
            reasons.append(f"预计性能提升 {predicted_gain:.1%}")
        
        return "；".join(reasons)
    
    def save_model(self):
        """保存模型到文件"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.feature_scaler,
                    'last_training_time': self.last_training_time,
                    'history_size': len(self.history)
                }, f)
        except Exception as e:
            print(f"[CachePredictor] 保存模型失败: {e}")
    
    def load_model(self):
        """从文件加载模型"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.feature_scaler = data.get('scaler')
                    self.last_training_time = data.get('last_training_time', 0)
                return True
        except Exception as e:
            print(f"[CachePredictor] 加载模型失败: {e}")
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取预测器统计信息"""
        return {
            'history_size': len(self.history),
            'predictions_count': len(self.predictions),
            'model_type': type(self.model).__name__ if self.model is not None else 'None',
            'last_training_time': self.last_training_time,
            'model_path': self.model_path,
            'training_interval': self.training_interval,
        }


# 全局预测器实例
_predictor_instance = None

def get_cache_predictor() -> CachePredictor:
    """获取全局缓存预测器实例"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = CachePredictor()
        _predictor_instance.load_model()
    return _predictor_instance


if __name__ == '__main__':
    # 简单测试
    predictor = CachePredictor()
    print("缓存分区预测器初始化完成")
    print(f"模型状态: {predictor.get_statistics()}")

