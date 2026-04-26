package com.ironion.mock;

import lombok.Getter;

/**
 * 场景类型枚举
 * 定义各种模拟的生产环境故障场景及其概率分布和日志级别
 */
public enum ScenarioType {
    
    // 正常请求 - 最高概率，模拟大部分正常流量
    NORMAL_REQUEST(70, "INFO"),
    
    // 慢请求 - 中等概率，模拟性能问题
    SLOW_REQUEST(10, "WARN"),
    
    // 数据库超时 - 较低概率，模拟数据库连接或查询超时
    DATABASE_TIMEOUT(3, "ERROR"),
    
    // 下游服务超时 - 较低概率，模拟依赖服务响应慢
    DOWNSTREAM_TIMEOUT(3, "ERROR"),
    
    // 空指针异常 - 低概率，模拟代码缺陷
    NULL_POINTER(2, "ERROR"),
    
    // 无效参数 - 低概率，模拟参数校验失败
    INVALID_ARGUMENT(2, "WARN"),
    
    // 业务数据错误 - 低概率，模拟数据不一致
    BUSINESS_DATA_ERROR(2, "ERROR"),
    
    // 订单状态不匹配 - 低概率，模拟业务流程异常
    ORDER_STATUS_MISMATCH(2, "ERROR"),
    
    // 库存不足 - 低概率，模拟库存业务问题
    INVENTORY_NOT_ENOUGH(2, "WARN"),
    
    // 支付状态错误 - 低概率，模拟支付流程异常
    PAYMENT_STATUS_ERROR(2, "ERROR"),
    
    // 工作流阻塞 - 低概率，模拟流程引擎问题
    WORKFLOW_BLOCKED(1, "ERROR"),
    
    // 重试中 - 中等概率，模拟临时故障的重试机制
    RETRYING(2, "WARN"),
    
    // 重试失败 - 低概率，模拟多次重试后仍失败
    RETRY_FAILED(1, "ERROR"),
    
    // 线程池压力 - 极低概率，模拟高负载情况
    THREAD_POOL_PRESSURE(1, "WARN");
    
    @Getter
    private final int probability; // 概率权重
    
    @Getter
    private final String logLevel; // 日志级别
    
    ScenarioType(int probability, String logLevel) {
        this.probability = probability;
        this.logLevel = logLevel;
    }
    
    public int getProbability() {
        return probability;
    }
    
    public String getLogLevel() {
        return logLevel;
    }
    
    /**
     * 根据概率权重随机选择场景
     * @return 选中的场景类型
     */
    public static ScenarioType randomScenario() {
        int totalWeight = 0;
        for (ScenarioType scenario : values()) {
            totalWeight += scenario.probability;
        }
        
        int random = (int) (Math.random() * totalWeight);
        int currentWeight = 0;
        
        for (ScenarioType scenario : values()) {
            currentWeight += scenario.probability;
            if (random < currentWeight) {
                return scenario;
            }
        }
        
        return NORMAL_REQUEST; // 默认返回正常请求
    }
}
