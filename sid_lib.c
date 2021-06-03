#include <pigpio.h>
#include <stdio.h>

#define INVF 16.777216 / 256
#define tone 96
#define current_vol 0

#define DIO 8 // eight data bits starting from 8
#define AIO 16 // five address bits starting from 16
#define RW 3
#define SID_RESET 2
#define CLK 4

uint32_t CSIO[] = {21,22,23,24,25,26,27,7};
uint32_t del = 0;

void out_bus(uint32_t dir) {
    if (dir) {
        dir = 1;
    } else {
        dir = 0;
    }
    for (uint32_t i=0; i<7; i++){
        gpioSetMode(i+DIO, dir);
    }      

}
    
void reset_sid() {
    gpioWrite_Bits_0_31_Clear(1<<SID_RESET);
    del = gpioDelay(50);    
    gpioWrite_Bits_0_31_Set(1<<SID_RESET);
    del = gpioDelay(50); 
}

void init_sid() {
   
    if (gpioInitialise() < 0) {
        printf( "pigpio initialisation failed.\n");
        //printf("Error code: %s", str);
    } 

    gpioSetMode(CLK, 0);
    
    for (uint32_t i=0; i<7; i++){
        if (i<5){
        gpioSetMode(i+AIO, 1);
        gpioWrite_Bits_0_31_Clear(1<<(AIO+i));
        }
        gpioSetMode(CSIO[i], 1);
        gpioWrite_Bits_0_31_Set(1<<CSIO[i]);
    }      
    gpioSetMode(RW, 1);
    gpioWrite_Bits_0_31_Clear( (1<<RW));

    gpioSetMode(SID_RESET, 1);   
    gpioWrite_Bits_0_31_Set(1<<SID_RESET);
    
    out_bus(1);
}    

void write_sid(uint32_t cs,uint32_t a,uint32_t d) {
    a = a & 31;
    cs = cs & 7;
    uint32_t inva = 31 - a; 
    gpioWrite_Bits_0_31_Set(a<<AIO);
    gpioWrite_Bits_0_31_Clear(inva<<AIO);
    
    d = d & 255;
    uint32_t invd = 255 - d; 
    gpioWrite_Bits_0_31_Set(d<<DIO);
    gpioWrite_Bits_0_31_Clear(invd<<DIO);
    
    del = gpioDelay(1);   
    
    gpioWrite_Bits_0_31_Clear( (1<<RW) | (1<<CSIO[cs]));
        
    del = gpioDelay(4);
        
    gpioWrite_Bits_0_31_Set(1<<CSIO[cs]);  

    del = gpioDelay(2);
    
}

int read_sid(uint32_t cs, uint32_t a) { // note: only registers 25-28 can be read on a SID
    out_bus(0); // make data bus input
    a = a & 31;
    cs = cs & 7;

    uint32_t inva = 31 - a;
    gpioWrite_Bits_0_31_Set(a<<AIO);
    gpioWrite_Bits_0_31_Clear(inva<<AIO);
    
    del = gpioDelay(5);
 
    gpioWrite_Bits_0_31_Set(1<<RW);
    
    del = gpioDelay(5);
    
    gpioWrite_Bits_0_31_Clear(1<<CSIO[cs]);   
           
    del = gpioDelay(20);
    
    uint32_t d = gpioRead_Bits_0_31();
    d = (d >> DIO) & 255;
            
    gpioWrite_Bits_0_31_Set(1<<CSIO[cs]);  
    gpioWrite_Bits_0_31_Clear(1<<RW);
    
    del = gpioDelay(1);
    
    out_bus(1); // Return data back to output because it is default to output
    
    return d;
}

/*
int main(int argc, char *argv[])
{

    if (gpioInitialise() < 0) {
        printf( "pigpio initialisation failed.\n");
    } else {
        printf( "pigpio initialisation OK\n");
    }
    out_bus(1);
    for (int  i; i<500; i++) { // little square wave test to check driver is working
        del = gpioDelay(1000);
        write_sid(0, 24, 0) ;
        del = gpioDelay(1000);
        write_sid(0, 24, 15) ;   
    }
    printf( "Program ended.\n");  
  return 0 ;
}

*/
