package com.ironion.mock;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

/**
 * Mock服务主应用
 * 启动后持续生成模拟的生产环境日志
 */
@Slf4j
@SpringBootApplication
public class MockServiceApplication {
    
    @Value("${mock.log.interval.min:2000}")
    private int minInterval;
    
    @Value("${mock.log.interval.max:5000}")
    private int maxInterval;
    
    @Value("${mock.log.error-rate:15}")
    private int errorRate;
    
    public static void main(String[] args) {
        SpringApplication.run(MockServiceApplication.class, args);
    }
    
    /**
     * 命令行运行器
     * 应用启动后开始无限循环生成日志
     */
    @Bean
    public CommandLineRunner startLogSimulation(LogSimulator simulator) {
        return args -> {
            log.info("=== Mock Service Started ===");
            log.info("开始生成模拟生产环境日志...");
            
            while (true) {
                try {
                    // 执行一次日志模拟
                    simulator.simulate();
                    
                    // 随机延迟（可配置）
                    int delay = (int) (Math.random() * (maxInterval - minInterval) + minInterval);
                    Thread.sleep(delay);
                    
                } catch (InterruptedException e) {
                    log.warn("日志模拟被中断", e);
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    log.error("日志模拟异常，继续执行", e);
                }
            }
        };
    }
}
