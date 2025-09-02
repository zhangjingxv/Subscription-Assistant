#!/usr/bin/env python3
"""
AttentionSync - Economic Approach
"注意力是最稀缺的资源" - Herbert Simon
"""

from typing import List, Dict, Tuple
import math
import time
from dataclasses import dataclass
from enum import Enum

class Market(Enum):
    """信息市场类型"""
    MONOPOLY = "unique_source"      # 独家信息
    OLIGOPOLY = "few_sources"        # 少数来源
    COMPETITION = "many_sources"     # 充分竞争
    PERFECT = "infinite_sources"     # 完全竞争

@dataclass
class InformationAsset:
    """信息资产"""
    content: str
    supply: float      # 供给量（有多少类似信息）
    demand: float      # 需求量（用户兴趣度）
    production_cost: float  # 生产成本（获取难度）
    consumption_cost: float # 消费成本（理解难度）
    depreciation_rate: float # 折旧率（时效性）
    
    @property
    def price(self) -> float:
        """价格 = f(供需关系)"""
        if self.supply == 0:
            return float('inf')
        return self.demand / self.supply
    
    @property
    def roi(self) -> float:
        """投资回报率"""
        total_cost = self.production_cost + self.consumption_cost
        if total_cost == 0:
            return float('inf')
        return (self.price - total_cost) / total_cost
    
    @property
    def present_value(self, time_elapsed: float = 0) -> float:
        """现值（考虑折旧）"""
        return self.price * (1 - self.depreciation_rate) ** time_elapsed


class AttentionEconomy:
    """
    注意力经济学模型
    核心理论：注意力是有限资源，信息消费遵循经济学规律
    """
    
    def __init__(self):
        # 用户的注意力预算
        self.attention_budget = 180  # 秒（3分钟）
        self.cognitive_budget = 7     # 项目数（Miller's Number）
        
        # 效用函数参数
        self.risk_aversion = 0.5     # 风险厌恶系数
        self.time_preference = 0.8   # 时间偏好（现在vs未来）
        
        # 市场状态
        self.market_equilibrium = {}
        self.price_history = []
    
    def utility_function(self, value: float, cost: float) -> float:
        """
        效用函数 - Cobb-Douglas生产函数的变体
        U = V^α * (B-C)^(1-α)
        其中V是价值，B是预算，C是成本，α是偏好参数
        """
        if cost >= self.attention_budget:
            return -float('inf')  # 预算约束
        
        remaining_budget = self.attention_budget - cost
        
        # 对数效用（边际效用递减）
        if value > 0 and remaining_budget > 0:
            utility = self.risk_aversion * math.log(value) + \
                     (1 - self.risk_aversion) * math.log(remaining_budget)
        else:
            utility = -float('inf')
        
        return utility
    
    def marginal_utility(self, items: List[InformationAsset], 
                        selected: List[int]) -> List[float]:
        """
        边际效用 - 增加一个项目带来的额外效用
        """
        marginal = []
        current_cost = sum(items[i].consumption_cost for i in selected)
        current_value = sum(items[i].price for i in selected)
        current_utility = self.utility_function(current_value, current_cost)
        
        for i, item in enumerate(items):
            if i not in selected:
                new_cost = current_cost + item.consumption_cost
                new_value = current_value + item.price
                new_utility = self.utility_function(new_value, new_cost)
                marginal.append(new_utility - current_utility)
            else:
                marginal.append(0)  # 已选择
        
        return marginal
    
    def supply_demand_analysis(self, items: List[Dict]) -> Dict[str, float]:
        """
        供需分析 - 确定信息的市场价值
        """
        
        # 统计供给（相似信息的数量）
        supply_map = {}
        for item in items:
            # 简单的主题识别（实际应该用更复杂的方法）
            keywords = set(item.get('content', '').lower().split()[:10])
            for keyword in keywords:
                supply_map[keyword] = supply_map.get(keyword, 0) + 1
        
        # 计算平均供给
        avg_supply = sum(supply_map.values()) / max(len(supply_map), 1)
        
        # 需求建模（基于历史点击、搜索等 - 这里简化）
        demand_map = {
            'breaking': 10,
            'exclusive': 9,
            'important': 8,
            'update': 5,
            'regular': 3
        }
        
        return {
            'avg_supply': avg_supply,
            'supply_variance': self.variance(list(supply_map.values())),
            'market_type': self.classify_market(avg_supply)
        }
    
    def variance(self, values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def classify_market(self, supply: float) -> Market:
        """市场分类"""
        if supply < 2:
            return Market.MONOPOLY
        elif supply < 5:
            return Market.OLIGOPOLY
        elif supply < 20:
            return Market.COMPETITION
        else:
            return Market.PERFECT
    
    def portfolio_optimization(self, assets: List[InformationAsset]) -> List[int]:
        """
        投资组合优化 - Markowitz现代投资组合理论
        目标：在风险约束下最大化收益
        """
        
        n = len(assets)
        if n == 0:
            return []
        
        # 动态规划解决背包问题
        # dp[i][j][k] = 前i个项目，时间预算j，认知预算k的最大效用
        
        # 简化：贪心算法（按ROI排序）
        indexed_assets = [(i, asset) for i, asset in enumerate(assets)]
        indexed_assets.sort(key=lambda x: x[1].roi, reverse=True)
        
        selected = []
        total_time = 0
        total_items = 0
        
        for idx, asset in indexed_assets:
            if total_time + asset.consumption_cost <= self.attention_budget and \
               total_items < self.cognitive_budget:
                selected.append(idx)
                total_time += asset.consumption_cost
                total_items += 1
        
        return selected
    
    def price_discovery(self, item: Dict, market_data: Dict) -> float:
        """
        价格发现机制 - 市场如何定价信息
        """
        
        content = item.get('content', '')
        
        # 基础价值
        base_value = len(set(content.split()))  # 独特词汇数
        
        # 市场调整
        market_type = market_data.get('market_type', Market.COMPETITION)
        if market_type == Market.MONOPOLY:
            multiplier = 5.0
        elif market_type == Market.OLIGOPOLY:
            multiplier = 2.0
        elif market_type == Market.COMPETITION:
            multiplier = 1.0
        else:
            multiplier = 0.5
        
        # 时间价值调整
        age = time.time() - item.get('timestamp', time.time())
        time_discount = 0.5 ** (age / 86400)  # 每天价值减半
        
        return base_value * multiplier * time_discount
    
    def arbitrage_opportunity(self, items: List[Dict]) -> List[Tuple[int, int, float]]:
        """
        套利机会 - 发现被低估的信息
        """
        
        opportunities = []
        
        for i, item1 in enumerate(items):
            price1 = self.price_discovery(item1, {})
            
            for j, item2 in enumerate(items):
                if i != j:
                    price2 = self.price_discovery(item2, {})
                    
                    # 相似内容但价格差异大
                    similarity = self.calculate_similarity(
                        item1.get('content', ''),
                        item2.get('content', '')
                    )
                    
                    if similarity > 0.8 and abs(price1 - price2) > 10:
                        profit = abs(price1 - price2) * similarity
                        opportunities.append((i, j, profit))
        
        return sorted(opportunities, key=lambda x: x[2], reverse=True)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def nash_equilibrium(self, items: List[Dict]) -> List[int]:
        """
        纳什均衡 - 多个信息源的博弈均衡
        每个信息源都在竞争用户的注意力
        """
        
        n = len(items)
        if n == 0:
            return []
        
        # 简化的博弈：每个项目的策略是"被选择"或"不被选择"
        # 收益矩阵基于互补性和替代性
        
        selected = []
        remaining = list(range(n))
        
        while remaining and len(selected) < self.cognitive_budget:
            best_response = None
            best_payoff = -float('inf')
            
            for i in remaining:
                # 计算选择i的收益
                payoff = self.price_discovery(items[i], {})
                
                # 考虑与已选项目的互补/替代关系
                for j in selected:
                    similarity = self.calculate_similarity(
                        items[i].get('content', ''),
                        items[j].get('content', '')
                    )
                    
                    if similarity > 0.7:  # 替代品
                        payoff *= (1 - similarity)  # 降低价值
                    elif similarity < 0.3:  # 互补品
                        payoff *= (1 + (1 - similarity))  # 提高价值
                
                if payoff > best_payoff:
                    best_payoff = payoff
                    best_response = i
            
            if best_response is not None:
                selected.append(best_response)
                remaining.remove(best_response)
            else:
                break
        
        return selected


class BehavioralEconomics:
    """
    行为经济学 - 考虑人类的非理性行为
    """
    
    def __init__(self):
        self.loss_aversion = 2.0  # 损失厌恶系数（Kahneman-Tversky）
        self.anchoring_bias = 0.3  # 锚定效应
        self.recency_bias = 0.5   # 近因效应
        
    def prospect_theory_value(self, outcome: float, reference: float = 0) -> float:
        """
        前景理论价值函数
        V(x) = x^α if x >= 0
        V(x) = -λ(-x)^α if x < 0
        """
        alpha = 0.88  # 风险态度参数
        
        gain_or_loss = outcome - reference
        
        if gain_or_loss >= 0:
            return gain_or_loss ** alpha
        else:
            return -self.loss_aversion * ((-gain_or_loss) ** alpha)
    
    def framing_effect(self, item: Dict, frame: str = "gain") -> float:
        """
        框架效应 - 同样的信息不同的表述影响决策
        """
        
        base_value = len(item.get('content', '').split())
        
        if frame == "gain":
            # "你将获得..."
            return base_value * 1.2
        elif frame == "loss":
            # "你将失去..."
            return base_value * self.loss_aversion
        else:
            return base_value
    
    def hyperbolic_discounting(self, value: float, delay: float) -> float:
        """
        双曲贴现 - 人们过度重视即时奖励
        V = V0 / (1 + k*t)
        """
        k = 0.1  # 贴现率
        return value / (1 + k * delay)


# === 实用接口 ===

def economic_selection(items: List[Dict]) -> Dict:
    """使用经济学模型选择信息"""
    
    economy = AttentionEconomy()
    
    # 创建信息资产
    assets = []
    market_data = economy.supply_demand_analysis(items)
    
    for item in items:
        asset = InformationAsset(
            content=item.get('content', ''),
            supply=market_data['avg_supply'],
            demand=10,  # 简化：固定需求
            production_cost=1,
            consumption_cost=len(item.get('content', '').split()) / 200 * 60,  # 阅读时间(秒)
            depreciation_rate=0.5  # 每天贬值50%
        )
        assets.append(asset)
    
    # 投资组合优化
    selected_indices = economy.portfolio_optimization(assets)
    
    # 纳什均衡选择
    equilibrium = economy.nash_equilibrium(items)
    
    return {
        'portfolio': [items[i] for i in selected_indices],
        'equilibrium': [items[i] for i in equilibrium],
        'market_type': market_data['market_type'].value,
        'total_roi': sum(assets[i].roi for i in selected_indices)
    }


if __name__ == '__main__':
    print("=== AttentionSync: Economic Approach ===\n")
    
    # 测试数据
    test_items = [
        {'content': 'Exclusive breaking news about market crash', 'timestamp': time.time()},
        {'content': 'Regular daily update on weather', 'timestamp': time.time() - 3600},
        {'content': 'Important announcement from government', 'timestamp': time.time() - 7200}
    ]
    
    result = economic_selection(test_items)
    
    print(f"Market Type: {result['market_type']}")
    print(f"Total ROI: {result['total_roi']:.2f}")
    print(f"Selected {len(result['portfolio'])} items by portfolio optimization")
    print(f"Selected {len(result['equilibrium'])} items by Nash equilibrium")
    
    print("\n=== Key Insight ===")
    print("世界级程序理解稀缺性。")
    print("注意力是终极稀缺资源。")
    print("信息选择是经济决策。")