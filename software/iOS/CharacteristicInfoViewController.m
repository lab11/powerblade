
#import "CharacteristicInfoViewController.h"
#import "Commom.h"
#import "BLEmanager.h"
#import "BlePeripheral.h"
@interface CharacteristicInfoViewController ()
{
    Commom *common;
    BLEmanager *m_bleManger;
}
@end

@implementation CharacteristicInfoViewController
@synthesize curCharacteristic, curBLE;

NSTimer *m_timer_threesec;
NSTimer *m_timer_fifteensec;


- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor whiteColor];
    common = [Commom sharedInstance];
    [self characteristicInfo:true];
    m_bleManger = [BLEmanager shareInstance];
    m_bleManger.mange_delegate = self;
    
    NSArray *services = [[NSArray alloc]init];
    [m_bleManger.m_manger scanForPeripheralsWithServices:nil options:@{ CBCentralManagerScanOptionAllowDuplicatesKey : @YES,CBCentralManagerScanOptionSolicitedServiceUUIDsKey : services }];
    m_timer_threesec=[NSTimer scheduledTimerWithTimeInterval:3.0 target:self selector:@selector(scanresult) userInfo:nil repeats:YES];
    m_timer_fifteensec=[NSTimer scheduledTimerWithTimeInterval:15.0 target:self selector:@selector(timeout) userInfo:nil repeats:YES];


}

-(void)viewWillAppear:(BOOL)animated {

}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning];
}

-(void)viewDidDisappear:(BOOL)animated {
    [m_bleManger.m_manger stopScan];
}

-(void)scanresult
{
    if ([m_bleManger.m_array_peripheral count]>0) {
        for (int i=0;i<[m_bleManger.m_array_peripheral count];i++) {
            BlePeripheral *tmp_per = [m_bleManger.m_array_peripheral objectAtIndex:i];
            if (curBLE.m_powerBladeID  == tmp_per.m_powerBladeID) {
                curBLE.m_rssi = tmp_per.m_rssi;
                curBLE.m_aPower = tmp_per.m_aPower;
                curBLE.m_flags = tmp_per.m_flags;
                curBLE.m_numConnections = tmp_per.m_numConnections;
                curBLE.m_pfactor = tmp_per.m_pfactor;
                curBLE.m_sequenceNum = tmp_per.m_sequenceNum;
                curBLE.m_time = tmp_per.m_time;
                curBLE.m_tPower = tmp_per.m_tPower;
                curBLE.m_vRMS = tmp_per.m_vRMS;
                curBLE.m_wHr = tmp_per.m_wHr;
                [self characteristicInfo:false];
                [m_timer_fifteensec invalidate];
                m_timer_fifteensec=[NSTimer scheduledTimerWithTimeInterval:15.0 target:self selector:@selector(timeout) userInfo:nil repeats:YES];
                NSLog(@"DEAR LORD HIT!");
            }
        }
    }
    
    NSLog(@"scan result");
    [self.view.subviews makeObjectsPerformSelector: @selector(removeFromSuperview)];
    [self characteristicInfo:false];
    [self setLabel];


}

-(void)timeout
{
    [self.navigationController popViewControllerAnimated:YES];
}

UILabel *powerLabel;
UILabel *largePower;
UIImage * powerBladeImg;
UIImage *scaledImage;
UIImageView *powerBladeImgView;
UILabel *powerBladeID;
UILabel * timeRec ;
UILabel *voltageRMS;
UILabel *currentTruePower;
UILabel *currentApparentPower;
UILabel *cumulativeWattHours;
UILabel *powerFactor;
UILabel *apparentPower;

UIView *topView;



-(void)characteristicInfo:(bool) isNew
{
    //[self.view.subviews makeObjectsPerformSelector: @selector(removeFromSuperview)];

    NSLog(@"characteristicInfo = %@",curCharacteristic.description);

    NSLog([NSString stringWithFormat: @"IN CHARACTERISTIC %ld", (long)curBLE.m_powerBladeID] );

    UIFont * labelFont = [UIFont fontWithName:@"Courier" size:14];
    

    powerBladeImg = [UIImage imageNamed:@"powerblade.png"];
    scaledImage =
    [UIImage imageWithCGImage:[powerBladeImg CGImage]
                        scale:(powerBladeImg.scale * 2.5)
                  orientation:(powerBladeImg.imageOrientation)];
    topView = [[UIView alloc] initWithFrame:CGRectMake(0,self.navigationController.navigationBar.frame.size.height, MainScreen_Width, scaledImage.size.height+self.navigationController.navigationBar.frame.size.height+10 )];
    topView.backgroundColor = [UIColor lightGrayColor];
    
    largePower = [[UILabel alloc] initWithFrame:CGRectMake(topView.frame.origin.x + MainScreen_Width/1.5-15, topView.frame.origin.y + MainScreen_Height/8, MainScreen_Width, 80)];
    largePower.font = [UIFont fontWithName:@"Courier" size:30];

    
    powerLabel = [[UILabel alloc]initWithFrame:CGRectMake(topView.frame.origin.x + MainScreen_Width/1.5, topView.frame.origin.y, MainScreen_Width, 40)];
    powerLabel.text     = [NSString stringWithFormat:@"Power"];
    powerLabel.tintColor = [UIColor purpleColor];
    powerLabel.font = [UIFont fontWithName:@"Courier" size:25];
    
    powerBladeImgView = [[UIImageView alloc] initWithImage:scaledImage];
    [powerBladeImgView setFrame:CGRectMake(topView.frame.origin.x + 20,topView.frame.origin.y - 10, scaledImage.size.width, scaledImage.size.height)];
    [topView addSubview:powerBladeImgView];
    [topView addSubview:powerLabel];
    [topView addSubview:largePower];

    
    
 
    
    powerBladeID = [[UILabel alloc]initWithFrame:CGRectMake(10, 300, MainScreen_Width-10, 40)];
    powerBladeID.font = labelFont;
//    UILabel *sequenceNum           = [[UILabel alloc]initWithFrame:CGRectMake(10, 225, MainScreen_Width-10, 40)];
    
    timeRec = [[UILabel alloc]initWithFrame:CGRectMake(10, 325, MainScreen_Width-10, 40)];
    timeRec.font = labelFont;
    
    voltageRMS = [[UILabel alloc]initWithFrame:CGRectMake(10, 350, MainScreen_Width-10, 40)];
    voltageRMS.font = labelFont;
    
    currentTruePower = [[UILabel alloc]initWithFrame:CGRectMake(10, 375, MainScreen_Width-10, 40)];
    currentTruePower.font = labelFont;
    
    currentApparentPower = [[UILabel alloc]initWithFrame:CGRectMake(10, 400, MainScreen_Width-10, 40)];
    currentApparentPower.font = labelFont;
    
    cumulativeWattHours    = [[UILabel alloc]initWithFrame:CGRectMake(10, 425, MainScreen_Width-10, 40)];
    cumulativeWattHours.font = labelFont;
    
    powerFactor     = [[UILabel alloc]initWithFrame:CGRectMake(10, 450, MainScreen_Width-10, 40)];
    powerFactor.font = labelFont;
    


    //    UILabel *flags     = [[UILabel alloc]initWithFrame:CGRectMake(10, 400, MainScreen_Width-10, 40)];
    //    UILabel *avgPower     = [[UILabel alloc]initWithFrame:CGRectMake(10, 425, MainScreen_Width-10, 40)];
    apparentPower     = [[UILabel alloc]initWithFrame:CGRectMake(10, 475, MainScreen_Width-10, 40)];
    apparentPower.font = labelFont;
    //    UILabel *wattHoursSinceStart     = [[UILabel alloc]initWithFrame:CGRectMake(10, 475, MainScreen_Width-10, 40)];
    //    UILabel *time_start     = [[UILabel alloc]initWithFrame:CGRectMake(10, 500, MainScreen_Width-10, 40)];
    //    UILabel *packetsLast30     = [[UILabel alloc]initWithFrame:CGRectMake(10, 525, MainScreen_Width-10, 40)];
    
    [self.view addSubview:topView];
    [self.view addSubview:powerBladeID];
//    [self.view addSubview:sequenceNum];
    [self.view addSubview:timeRec];
    [self.view addSubview:voltageRMS];
    [self.view addSubview:currentTruePower];
    [self.view addSubview:currentApparentPower];
    [self.view addSubview:cumulativeWattHours];
    [self.view addSubview:powerFactor];
//    [self.view addSubview:flags];
//    [self.view addSubview:avgPower];
    [self.view addSubview:apparentPower];
//    [self.view addSubview:wattHoursSinceStart];
//    [self.view addSubview:time_start];
//    [self.view addSubview:packetsLast30];
    [self setLabel];
}

-(void) setLabel {
    powerBladeID.text     = [NSString stringWithFormat:@"PowerBlade ID:  %ld",(long)curBLE.m_powerBladeID];
    //    sequenceNum.text     = [NSString stringWithFormat:@"Sequence Number:  %ld",(long)curBLE.m_sequenceNum];
    //timeRec.text     = [NSString stringWithFormat:@"Time:  %.2ld",(long)curBLE.m_time];
    NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
    [timeFormatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
    [timeFormatter setTimeZone:[NSTimeZone timeZoneWithName:@"GMT"]];
    NSString * newTime = [timeFormatter stringFromDate:[[NSDate alloc]init] ];
    timeRec.text = [NSString stringWithFormat:@"Time Last Rec: %@", newTime];
    
    largePower.text = [NSString stringWithFormat:@"%.0f W", curBLE.m_tPower];
    voltageRMS.text     = [NSString stringWithFormat:@"RMS Voltage:  %.2f V",curBLE.m_vRMS];
    currentTruePower.text     = [NSString stringWithFormat:@"Current True Power:  %.2f W", curBLE.m_tPower];
    currentApparentPower.text     = [NSString stringWithFormat:@"Current Apparent Power: %.2f VA",curBLE.m_aPower];
    cumulativeWattHours.text     = [NSString stringWithFormat:@"Cumulative Watt Hours: %.2f Wh",curBLE.m_wHr];
    powerFactor.text     = [NSString stringWithFormat:@"Power Factor: %.2f", curBLE.m_pfactor];
    //    flags.text     = [NSString stringWithFormat:@"Flags:  %ld",(long)curBLE.m_flags];
    //    avgPower.text     = [NSString stringWithFormat:@"Average Power (10):  %ld",(long)curBLE.m_avgPower];
    //    apparentPower.text     = [NSString stringWithFormat:@"Apparent Power: %.2f",curBLE.m_aPower];
    //    wattHoursSinceStart.text     = [NSString stringWithFormat:@"Watt Hours Since Start:  %ld",(long)curBLE.m_whrStart];
    //    time_start.text     = [NSString stringWithFormat:@"Time:  %ld",(long)curBLE.m_time_since_start];
    //    packetsLast30.text     = [NSString stringWithFormat:@"Packets in last 30s: %ld",(long)curBLE.m_packets_last_30];
}

@end
