#!/usr/bin/env python3
"""
AttentionSync - Biological Approach
"注意力是生存的进化优势" - 从生物学理解信息处理
"""

import random
import time
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

class Neurotransmitter(Enum):
    """神经递质 - 不同信息类型触发不同反应"""
    DOPAMINE = "reward"      # 奖励信号 - 重要发现
    SEROTONIN = "mood"       # 情绪调节 - 正面内容
    NOREPINEPHRINE = "alert" # 警觉信号 - 紧急信息
    GABA = "inhibit"         # 抑制信号 - 过滤噪音
    ACETYLCHOLINE = "learn"  # 学习信号 - 新知识

@dataclass
class Neuron:
    """神经元 - 信息处理单元"""
    id: str
    threshold: float = 0.5
    potential: float = 0.0
    connections: Set['Neuron'] = None
    neurotransmitter: Neurotransmitter = Neurotransmitter.DOPAMINE
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = set()
    
    def receive(self, signal: float) -> bool:
        """接收信号"""
        self.potential += signal
        if self.potential >= self.threshold:
            self.fire()
            return True
        return False
    
    def fire(self):
        """激发 - 传递信号"""
        for neuron in self.connections:
            neuron.receive(self.potential * 0.7)  # 衰减传递
        self.potential = 0  # 重置

class AttentionCortex:
    """
    注意力皮层 - 模拟大脑的注意力机制
    基于神经科学的注意力模型
    """
    
    def __init__(self):
        # 工作记忆 (前额叶皮层)
        self.working_memory = []
        self.memory_capacity = 7  # Miller's Magic Number
        
        # 显著性地图 (顶叶)
        self.saliency_map = {}
        
        # 情绪中心 (杏仁核)
        self.emotional_weight = 1.0
        
        # 奖励系统 (伏隔核)
        self.reward_history = []
        
        # 习惯化 (海马体)
        self.seen_patterns = set()
        
        # 生物节律
        self.circadian_phase = self.get_circadian_phase()
    
    def get_circadian_phase(self) -> float:
        """获取生物节律相位 - 影响注意力水平"""
        hour = time.localtime().tm_hour
        
        # 注意力高峰期
        if 9 <= hour <= 11:  # 上午高峰
            return 1.0
        elif 14 <= hour <= 16:  # 下午低谷
            return 0.6
        elif 19 <= hour <= 21:  # 晚间次高峰
            return 0.8
        else:
            return 0.7
    
    def compute_saliency(self, stimulus: Dict) -> float:
        """
        计算显著性 - 什么会抓住注意力
        基于视觉注意力的生物学模型
        """
        
        saliency = 0.0
        content = stimulus.get('content', '')
        
        # 1. 新颖性检测 (Novelty Detection)
        content_hash = hash(content)
        if content_hash not in self.seen_patterns:
            saliency += 0.3
            self.seen_patterns.add(content_hash)
        
        # 2. 威胁检测 (Threat Detection) - 进化优先级
        threat_words = ['danger', 'warning', 'alert', 'critical', 'urgent']
        for word in threat_words:
            if word in content.lower():
                saliency += 0.5
                break
        
        # 3. 奖励预测 (Reward Prediction)
        reward_words = ['success', 'breakthrough', 'discovery', 'profit', 'win']
        for word in reward_words:
            if word in content.lower():
                saliency += 0.3
                break
        
        # 4. 社交相关 (Social Relevance) - 人类特有
        social_words = ['people', 'team', 'community', 'friend', 'family']
        for word in social_words:
            if word in content.lower():
                saliency += 0.2
                break
        
        # 5. 运动检测 (Motion Detection) - 变化的信息
        if stimulus.get('timestamp', 0) > time.time() - 3600:  # 最近1小时
            saliency += 0.2
        
        # 生物节律调节
        saliency *= self.circadian_phase
        
        return min(saliency, 1.0)
    
    def emotional_tagging(self, content: str) -> Neurotransmitter:
        """
        情绪标记 - 杏仁核的作用
        不同情绪影响记忆强度
        """
        
        content_lower = content.lower()
        
        # 简单的情绪识别
        if any(w in content_lower for w in ['success', 'win', 'achieve']):
            return Neurotransmitter.DOPAMINE
        elif any(w in content_lower for w in ['happy', 'joy', 'positive']):
            return Neurotransmitter.SEROTONIN
        elif any(w in content_lower for w in ['urgent', 'alert', 'warning']):
            return Neurotransmitter.NOREPINEPHRINE
        elif any(w in content_lower for w in ['new', 'learn', 'discover']):
            return Neurotransmitter.ACETYLCHOLINE
        else:
            return Neurotransmitter.GABA
    
    def consolidate_memory(self, items: List[Dict]) -> List[Dict]:
        """
        记忆巩固 - 模拟睡眠中的记忆整理
        保留重要信息，遗忘次要细节
        """
        
        # 计算每个项目的记忆强度
        memory_strength = []
        
        for item in items:
            strength = 0.0
            
            # 显著性贡献
            strength += self.compute_saliency(item) * 0.4
            
            # 情绪贡献
            emotion = self.emotional_tagging(item.get('content', ''))
            if emotion in [Neurotransmitter.DOPAMINE, Neurotransmitter.NOREPINEPHRINE]:
                strength += 0.3
            
            # 重复强化
            content = item.get('content', '')
            for past_item in self.working_memory:
                if self.similarity(content, past_item.get('content', '')) > 0.5:
                    strength += 0.1
            
            # 时间衰减
            age = time.time() - item.get('timestamp', time.time())
            strength *= (0.5 ** (age / 86400))  # 半衰期1天
            
            memory_strength.append((strength, item))
        
        # 选择强记忆
        memory_strength.sort(reverse=True)
        consolidated = []
        
        for strength, item in memory_strength[:self.memory_capacity]:
            if strength > 0.3:  # 记忆阈值
                consolidated.append(item)
        
        return consolidated
    
    def similarity(self, text1: str, text2: str) -> float:
        """计算相似度 - 简单的Jaccard相似度"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def attention_filter(self, stimuli: List[Dict]) -> List[Dict]:
        """
        注意力过滤器 - 视网膜神经节细胞的中心-周围拮抗
        增强重要信息，抑制背景噪音
        """
        
        if not stimuli:
            return []
        
        # 计算显著性地图
        for stimulus in stimuli:
            self.saliency_map[id(stimulus)] = self.compute_saliency(stimulus)
        
        # 侧抑制 - 相似内容互相抑制
        for i, stim1 in enumerate(stimuli):
            for j, stim2 in enumerate(stimuli):
                if i != j:
                    sim = self.similarity(
                        stim1.get('content', ''),
                        stim2.get('content', '')
                    )
                    if sim > 0.7:  # 高度相似
                        # 抑制较弱的信号
                        id1, id2 = id(stim1), id(stim2)
                        if self.saliency_map[id1] < self.saliency_map[id2]:
                            self.saliency_map[id1] *= (1 - sim)
                        else:
                            self.saliency_map[id2] *= (1 - sim)
        
        # 选择高显著性项目
        filtered = []
        for stimulus in stimuli:
            if self.saliency_map[id(stimulus)] > 0.4:
                filtered.append(stimulus)
        
        # 限制在工作记忆容量内
        filtered.sort(key=lambda x: self.saliency_map[id(x)], reverse=True)
        return filtered[:self.memory_capacity]


class EvolutionaryOptimizer:
    """
    进化优化器 - 用遗传算法优化信息选择
    模拟自然选择过程
    """
    
    def __init__(self, population_size: int = 50):
        self.population_size = population_size
        self.generations = 0
        self.fitness_history = []
    
    def fitness(self, genome: List[int], items: List[Dict], time_limit: int = 180) -> float:
        """
        适应度函数 - 评估基因组的生存能力
        基因组：选择哪些信息项的二进制串
        """
        
        if len(genome) != len(items):
            return 0.0
        
        total_value = 0.0
        total_time = 0.0
        selected_count = 0
        
        for i, gene in enumerate(genome):
            if gene == 1:
                item = items[i]
                # 价值：信息量
                value = len(set(item.get('content', '').split()))
                total_value += value
                
                # 成本：阅读时间
                read_time = len(item.get('content', '').split()) / 3  # 3词/秒
                total_time += read_time
                selected_count += 1
        
        # 惩罚超时
        if total_time > time_limit:
            total_value *= (time_limit / total_time)
        
        # 惩罚过多项目（认知负载）
        if selected_count > 7:
            total_value *= (7 / selected_count)
        
        return total_value
    
    def evolve(self, items: List[Dict], generations: int = 10) -> List[Dict]:
        """
        进化选择 - 多代进化找到最优组合
        """
        
        n_items = len(items)
        if n_items == 0:
            return []
        
        # 初始种群 - 随机基因组
        population = []
        for _ in range(self.population_size):
            genome = [random.randint(0, 1) for _ in range(n_items)]
            population.append(genome)
        
        # 进化循环
        for gen in range(generations):
            # 评估适应度
            fitness_scores = [
                (self.fitness(genome, items), genome)
                for genome in population
            ]
            fitness_scores.sort(reverse=True)
            
            # 记录最佳适应度
            self.fitness_history.append(fitness_scores[0][0])
            
            # 选择 - 保留前50%
            survivors = [genome for _, genome in fitness_scores[:self.population_size//2]]
            
            # 繁殖 - 交叉和变异
            new_population = survivors.copy()
            
            while len(new_population) < self.population_size:
                # 选择父母
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)
                
                # 交叉
                crossover_point = random.randint(1, n_items - 1)
                child = parent1[:crossover_point] + parent2[crossover_point:]
                
                # 变异
                if random.random() < 0.1:  # 10%变异率
                    mutation_point = random.randint(0, n_items - 1)
                    child[mutation_point] = 1 - child[mutation_point]
                
                new_population.append(child)
            
            population = new_population
        
        # 返回最优解
        best_genome = fitness_scores[0][1]
        selected_items = [
            items[i] for i, gene in enumerate(best_genome) if gene == 1
        ]
        
        return selected_items


# === 实用接口 ===

def biological_attention(items: List[Dict]) -> List[Dict]:
    """使用生物学模型处理信息"""
    
    # 初始化大脑
    cortex = AttentionCortex()
    
    # 注意力过滤
    filtered = cortex.attention_filter(items)
    
    # 记忆巩固
    consolidated = cortex.consolidate_memory(filtered)
    
    return consolidated


def evolutionary_selection(items: List[Dict]) -> List[Dict]:
    """使用进化算法选择信息"""
    
    optimizer = EvolutionaryOptimizer()
    selected = optimizer.evolve(items, generations=20)
    
    return selected


if __name__ == '__main__':
    print("=== AttentionSync: Biological Approach ===\n")
    
    # 模拟数据
    test_items = [
        {
            'content': 'Breaking news about important discovery in science',
            'timestamp': time.time() - 3600
        },
        {
            'content': 'Regular update about daily activities and events',
            'timestamp': time.time() - 7200
        },
        {
            'content': 'Urgent warning about critical system failure',
            'timestamp': time.time() - 1800
        }
    ]
    
    # 生物学处理
    cortex = AttentionCortex()
    
    print("Circadian Phase:", cortex.circadian_phase)
    print("\nSaliency Scores:")
    for item in test_items:
        score = cortex.compute_saliency(item)
        print(f"  {item['content'][:50]}... -> {score:.2f}")
    
    print("\n=== Key Insight ===")
    print("世界级程序向自然学习。")
    print("35亿年的进化已经解决了注意力分配问题。")
    print("我们只需要理解并模拟它。")