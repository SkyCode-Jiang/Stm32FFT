# STM32FFT

V1.0 

STM32F103C8T6内置ADC+光电池采集数据



串口重定向：

​	“Target”标签页勾选其中的“Use MicroLIB”选项

```cpp
int fputc(int ch,FILE *f)
{
//轮询发送1字节数据，无限等待
HAL_UART_Transmit(&huart1,(uint8_t *)&ch,1,HAL_MAX_DELAY);
return ch;
}
```

ADC：12位( 4095) 转换后*1000 到mv

​       采样率500Hz，1024个点做FFT，精度500/1024 = 0.488

定时器周期完成ADC采样，采样数据DMA传输,内置ADC采样率500Hz

[【STM32】HAL库 STM32CubeMX教程九---ADC_cubemx adc-CSDN博客](https://blog.csdn.net/as480133937/article/details/99627062)

[STM32Cubemx 配置ADC(HAL库）_stm32cubemx adc-CSDN博客](https://blog.csdn.net/m0_61973119/article/details/143055637)

[STM32CubeMX | HAL库的ADC多通道数据采集（轮训、DMA、DMA+TIM)、读取内部传感器温度_tim+adc+dma采集-CSDN博客](https://blog.csdn.net/qq153471503/article/details/108123019)

[STM32HAL ADC+TIM+DMA采集交流信号 基于cubemx_tim+adc+dma-CSDN博客](https://blog.csdn.net/qq_34022877/article/details/121941236)

[STM32CUBEMX配置教程（十二）STM32的定时器触发的固定频率ADC采样（使用DMA）_定时器溢出踩adc-CSDN博客](https://blog.csdn.net/weixin_44584198/article/details/119453399)

V2.0 PCB绘制



需要

刺激界面：

matlab处理程序：