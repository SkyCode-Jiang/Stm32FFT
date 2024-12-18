/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "spi.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <math.h>
#include "stm32_dsp.h"
#include "table_fft.h"
#include "lcd_init.h"
#include "lcd.h"
#include "pic.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
extern  UART_HandleTypeDef huart1;

int fputc(int ch, FILE *f)
{
		HAL_UART_Transmit(&huart1 ,(uint8_t *)&ch,1,HAL_MAX_DELAY);
	  return ch;
 }
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
#define  FFTNUM  1024          
long  lBufInArray[FFTNUM];    /* FFT IN */
long  lBufOutArray[FFTNUM/2]; /* FFT OUT */
long  lBufMagArray[FFTNUM/2];
 
#define NUM 1024
uint16_t lightbuffer[NUM];
volatile uint8_t AdcConvEnd = 0;
uint16_t MAX_Index = 0;
uint16_t MAX_Value = 0;
char showstr[50];
// 0.4883
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void GetPowerMag(void)
{
  s16 lx,ly;
	u32 i;
	MAX_Value = 0;
	MAX_Index = 0;
	for(i=0;i<FFTNUM/2;i++)//??FFT?????????????????,???????
	{
		lx = (lBufOutArray[i] << 16)>>16;      //?????,??
		ly = (lBufOutArray[i] >> 16);          //?????,??
		float X = FFTNUM*((float)lx)/32768;
		float Y = FFTNUM*((float)ly)/32768;
		float Mag = sqrt(X*X+Y*Y)/FFTNUM;
		if(i == 0){
           lBufMagArray[i] = (unsigned long)(Mag * 32768);
		}
        else{
           lBufMagArray[i] = (unsigned long)(Mag * 65536);
					if(lBufMagArray[i] >= MAX_Value)
					{
						MAX_Value =lBufMagArray[i];
						MAX_Index = i;
					}
					 
    }

	}
	//  FFT结果输出
  	printf("当前闪烁频率为 %.3f\r\n", (MAX_Index)*500.0/1024);	
    sprintf(showstr, "%.3f", (MAX_Index)*500.0/1024);
}


//快排
int quick_sort(long *a, int low, int high)
{
	int i = low;	
	int j = high;	
	long key = a[i]; 
	while (i < j)
	{
		while(i < j && a[j] >= key)
		{
			j--;
		}
		a[i] = a[j];	
		while(i < j && a[i] <= key)
		{
			i++;
		}
		a[j] = a[i];
	}
	a[i] = key;
	if (i-1 > low) 
	{
		quick_sort(a, low, i-1);
	} 
	if (i+1 < high)
	{
		quick_sort(a, i+1, high);
	} 
	return 0;
} 


/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_TIM3_Init();
  MX_SPI1_Init();
  /* USER CODE BEGIN 2 */
	HAL_TIM_Base_Start(&htim3);                          
	HAL_ADC_Start_DMA(&hadc1, (uint32_t *)lightbuffer, NUM); 
	
	printf("start test\r\n");
	float t=0;
  LCD_Init();//LCD初始化
	LCD_Fill(0,0,LCD_W,LCD_H,WHITE);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {

		while (!AdcConvEnd) ;   
		AdcConvEnd   = 0; 
//	  ADC结果输出
//		for (uint16_t i = 0; i < NUM; i++)
//		{
//			printf("%.5f\r\n", lightbuffer[i] * 3.3 / 4095 *1000 ); //mV
//		}	
	 	for (uint16_t i = 0; i < NUM; i++)
		{
			lBufInArray[i] = ((signed short)lightbuffer[i] - 2048) << 16 ;
		}	 
		cr4_fft_1024_stm32(lBufOutArray,lBufInArray, FFTNUM);

	  GetPowerMag();
//	//5 - 10Hz 0.4883 一共12个点   屏幕太小了 显示不全
//  	for(int i=10;i<21;i++)
//	 {
//		u16 dx = 128 / 12;
//		u16 x1 = dx * (i-10);
//		u16 x2 = x1 + dx;
//		LCD_DrawLine(x1,lBufMagArray[i]/8,x2,lBufMagArray[i+1]/8,RED);
//   }
//	LCD_ShowString(0,100,"5  6  7  8  9 10",RED,WHITE,16,0);
      LCD_ShowString(10,20,"Stim Freq",RED,WHITE,16,0);
		  //LCD_ShowFloatNum1(72,50,(MAX_Index-1)*500.0/1024,3,RED,WHITE,16);
		 LCD_ShowString(50,70,showstr,RED,WHITE,16,0);
//    FFT结果输出
//		printf("%ld\r\n", lBufMagArray[i] );	


    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

