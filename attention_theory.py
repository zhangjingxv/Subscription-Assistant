#!/usr/bin/env python3
"""
AttentionSync - Information Theory Approach
"Information is the resolution of uncertainty" - Claude Shannon
"""

import math
import hashlib
import time
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import json

class InformationEngine:
    """
    核心理论：信息的价值 = 新颖度 × 相关度 × 时效性
    """
    
    def __init__(self):
        self.history = defaultdict(list)  # 历史模式
        self.patterns = Counter()         # 模式识别
        self.decay_rate = 0.5             # 信息衰减率
        
    def entropy(self, text: str) -> float:
        """计算信息熵 - 衡量信息量"""
        if not text:
            return 0
        
        # 字符频率
        freq = Counter(text.lower())
        total = len(text)
        
        # Shannon熵
        entropy = 0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def novelty(self, content: str, context: List[str]) -> float:
        """计算新颖度 - 与已知信息的差异"""
        if not context:
            return 1.0
        
        # 内容指纹
        content_hash = set(content.lower().split())
        
        # 计算与历史内容的重叠
        overlap_scores = []
        for past in context[-10:]:  # 只看最近10条
            past_hash = set(past.lower().split())
            if past_hash:
                overlap = len(content_hash & past_hash) / len(content_hash | past_hash)
                overlap_scores.append(overlap)
        
        if overlap_scores:
            avg_overlap = sum(overlap_scores) / len(overlap_scores)
            return 1 - avg_overlap
        
        return 1.0
    
    def relevance(self, content: str, interests: Dict[str, float]) -> float:
        """计算相关度 - 与用户兴趣的匹配"""
        if not interests:
            return 0.5  # 无偏好时中性
        
        score = 0
        content_lower = content.lower()
        
        for keyword, weight in interests.items():
            if keyword.lower() in content_lower:
                # 关键词位置权重（标题中出现权重更高）
                position_weight = 2.0 if content_lower.index(keyword.lower()) < 100 else 1.0
                score += weight * position_weight
        
        # 归一化到0-1
        max_possible = sum(interests.values()) * 2
        return min(score / max_possible, 1.0) if max_possible > 0 else 0.5
    
    def timeliness(self, timestamp: int, current_time: int = None) -> float:
        """计算时效性 - 指数衰减"""
        if current_time is None:
            current_time = int(time.time())
        
        age_hours = (current_time - timestamp) / 3600
        
        # 指数衰减：24小时后价值减半
        return math.exp(-self.decay_rate * age_hours / 24)
    
    def information_value(self, content: str, timestamp: int, 
                         context: List[str], interests: Dict[str, float]) -> float:
        """
        核心算法：计算信息价值
        Value = Entropy × Novelty × Relevance × Timeliness
        """
        e = self.entropy(content)
        n = self.novelty(content, context)
        r = self.relevance(content, interests)
        t = self.timeliness(timestamp)
        
        # 加权组合（可调整权重）
        value = (e * 0.2) * (n * 0.3) * (r * 0.3) * (t * 0.2)
        
        return value
    
    def compress(self, text: str, target_length: int = 100) -> str:
        """
        信息压缩 - 保留最大信息量的压缩
        基于信息论：保留高熵部分
        """
        if len(text) <= target_length:
            return text
        
        # 句子级别压缩
        sentences = text.split('. ')
        if not sentences:
            return text[:target_length]
        
        # 计算每个句子的信息密度
        sentence_values = []
        for sent in sentences:
            if sent:
                density = self.entropy(sent) / max(len(sent), 1)
                sentence_values.append((density, sent))
        
        # 按信息密度排序
        sentence_values.sort(reverse=True)
        
        # 选择高密度句子直到达到目标长度
        result = []
        current_length = 0
        
        for _, sent in sentence_values:
            if current_length + len(sent) <= target_length:
                result.append(sent)
                current_length += len(sent)
            elif current_length == 0:
                # 至少包含一个句子
                result.append(sent[:target_length])
                break
        
        return '. '.join(result)


class AttentionManager:
    """
    注意力管理器 - 基于认知科学
    Miller's Law: 人类工作记忆只能处理 7±2 个项目
    """
    
    def __init__(self):
        self.engine = InformationEngine()
        self.attention_budget = 7  # 认知负载上限
        self.reading_speed = 200   # 平均阅读速度(词/分钟)
        
    def select_items(self, items: List[Dict], 
                    interests: Dict[str, float],
                    time_budget: int = 180) -> List[Dict]:
        """
        选择最优信息组合
        目标：在3分钟内传递最大价值
        
        这是一个背包问题的变种：
        - 容量：时间（3分钟）和认知负载（7项）
        - 价值：信息价值
        - 成本：阅读时间
        """
        
        if not items:
            return []
        
        # 计算每个项目的价值和成本
        evaluated_items = []
        context = [item.get('content', '') for item in items[-20:]]  # 历史上下文
        
        for item in items:
            content = item.get('content', '')
            timestamp = item.get('timestamp', int(time.time()))
            
            # 计算信息价值
            value = self.engine.information_value(
                content, timestamp, context, interests
            )
            
            # 计算阅读成本（秒）
            word_count = len(content.split())
            read_time = (word_count / self.reading_speed) * 60
            
            # 价值密度 = 价值 / 时间成本
            if read_time > 0:
                density = value / read_time
            else:
                density = 0
            
            evaluated_items.append({
                'item': item,
                'value': value,
                'cost': read_time,
                'density': density
            })
        
        # 贪心算法：选择价值密度最高的项目
        evaluated_items.sort(key=lambda x: x['density'], reverse=True)
        
        selected = []
        total_time = 0
        
        for eval_item in evaluated_items:
            if len(selected) >= self.attention_budget:
                break
            if total_time + eval_item['cost'] <= time_budget:
                selected.append(eval_item['item'])
                total_time += eval_item['cost']
        
        return selected
    
    def generate_digest(self, items: List[Dict], 
                       interests: Dict[str, float] = None) -> Dict:
        """
        生成智能摘要
        不是简单截取，而是基于信息论的压缩
        """
        
        if interests is None:
            interests = self.learn_interests(items)
        
        # 选择最有价值的项目
        selected = self.select_items(items, interests)
        
        # 生成摘要
        digest = {
            'timestamp': int(time.time()),
            'item_count': len(selected),
            'estimated_reading_time': 3,  # 分钟
            'items': []
        }
        
        for item in selected:
            # 智能压缩内容
            compressed = self.engine.compress(
                item.get('content', ''),
                target_length=200
            )
            
            digest['items'].append({
                'title': item.get('title', 'Untitled'),
                'summary': compressed,
                'url': item.get('url', ''),
                'value_score': self.engine.information_value(
                    item.get('content', ''),
                    item.get('timestamp', int(time.time())),
                    [],
                    interests
                )
            })
        
        # 按价值排序
        digest['items'].sort(key=lambda x: x['value_score'], reverse=True)
        
        return digest
    
    def learn_interests(self, items: List[Dict]) -> Dict[str, float]:
        """
        自动学习用户兴趣
        基于词频和共现分析
        """
        
        # 统计词频
        word_freq = Counter()
        bigram_freq = Counter()
        
        for item in items:
            words = item.get('content', '').lower().split()
            
            # 过滤停用词和短词
            words = [w for w in words if len(w) > 4]
            
            word_freq.update(words)
            
            # 二元组（相邻词对）
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                bigram_freq[bigram] = bigram_freq.get(bigram, 0) + 1
        
        # 提取高频关键词
        interests = {}
        
        # 单词权重
        for word, count in word_freq.most_common(10):
            if count > 2:  # 至少出现3次
                interests[word] = count / sum(word_freq.values())
        
        # 二元组权重（更高）
        for bigram, count in bigram_freq.most_common(5):
            if count > 1:  # 至少出现2次
                interests[bigram] = (count / sum(bigram_freq.values())) * 2
        
        return interests


# === 实用接口 ===

def process_feeds(feed_urls: List[str]) -> Dict:
    """处理多个Feed源"""
    
    manager = AttentionManager()
    all_items = []
    
    # 模拟获取数据（实际应该从RSS获取）
    for url in feed_urls:
        # 这里应该是真实的RSS解析
        items = [
            {
                'title': f'Article from {url}',
                'content': 'Sample content ' * 50,
                'url': url,
                'timestamp': int(time.time()) - 3600
            }
        ]
        all_items.extend(items)
    
    # 生成智能摘要
    digest = manager.generate_digest(all_items)
    
    return digest


def analyze_information_quality(text: str) -> Dict:
    """分析信息质量"""
    
    engine = InformationEngine()
    
    return {
        'entropy': engine.entropy(text),
        'compression_ratio': len(engine.compress(text)) / len(text),
        'estimated_reading_time': len(text.split()) / 200,  # 分钟
        'information_density': engine.entropy(text) / max(len(text), 1)
    }


if __name__ == '__main__':
    # 演示
    print("=== AttentionSync: Information Theory Approach ===\n")
    
    # 测试文本
    test_text = """
    The Linux kernel is the core of the Linux operating system. 
    It manages hardware resources and provides essential services. 
    Linus Torvalds created Linux in 1991 as a free alternative.
    The kernel uses a monolithic architecture for performance.
    """
    
    analysis = analyze_information_quality(test_text)
    
    print(f"Information Entropy: {analysis['entropy']:.2f} bits")
    print(f"Compression Ratio: {analysis['compression_ratio']:.2%}")
    print(f"Reading Time: {analysis['estimated_reading_time']:.1f} minutes")
    print(f"Information Density: {analysis['information_density']:.4f}")
    
    print("\n=== Key Insight ===")
    print("世界级程序不是代码少，而是理解深。")
    print("这个程序用信息论解决了注意力分配问题。")