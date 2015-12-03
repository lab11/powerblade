
#import "ViewController.h"
#import "BLEmanager.h"
#import "BlePeripheral.h"
#import "CharacteristicInfoViewController.h"
#import "AppDelegate.h"
#import "Commom.h"
#import "Header.h"
#import "MBProgressHUD.h"

@interface ViewController ()<UITableViewDataSource,UITableViewDelegate,BLEMangerDelegate>
{
    BLEmanager *m_bleManger;
    UITableView *m_tableView_peripheral;
    
    NSTimer *m_timer_threesec;  //3s
    NSTimer *m_timer_Connect;   //10s
    NSTimer *m_timer_fifteensec;   //10s

    
    Commom *common;

    BlePeripheral *m_current_peripheralInfo;
    MBProgressHUD *showConnectingHUD;
}
@end

@implementation ViewController

UIBarButtonItem *ScanButton;
UIRefreshControl * refreshControl;
bool isRefreshIconsOverlap = NO;
bool isRefreshAnimating = NO;
UIImageView * compass_background;
UIImageView * compass_spinner;
UIView * refreshColorView;
UIView * refreshLoadingView;
NSMutableDictionary *seq_map;
NSMutableDictionary *seq_map_time;
NSMutableDictionary *cur_dirty;



- (void)viewDidLoad {
    [super viewDidLoad];
    // Do any additional setup after loading the view, typically from a nib.
    
    common = [Commom sharedInstance];
    
    seq_map = [NSMutableDictionary dictionary];
    seq_map_time = [NSMutableDictionary dictionary];
    cur_dirty = [NSMutableDictionary dictionary];

    
    AppDelegate *appdelegate = [UIApplication sharedApplication].delegate;
    UINavigationController *rootNAV = [[UINavigationController alloc]initWithRootViewController:self];
    appdelegate.window.rootViewController = rootNAV;
    self.navigationController.navigationBarHidden = NO;
    
    /*
    ScanButton = [[UIBarButtonItem alloc] initWithTitle:@"Start Scanning" style:UIBarButtonItemStylePlain target:self action:@selector(scanPeripheralResult:)];
     */
    self.navigationItem.rightBarButtonItem = ScanButton;
    self.navigationItem.title = @"PowerBlade";

     
    m_timer_threesec=[NSTimer scheduledTimerWithTimeInterval:3.0 target:self selector:@selector(scanresult) userInfo:nil repeats:YES];
    m_timer_fifteensec=[NSTimer scheduledTimerWithTimeInterval:2.0 target:self selector:@selector(scanresult) userInfo:nil repeats:YES];

    
    m_tableView_peripheral = [[UITableView alloc]initWithFrame:CGRectMake(0, 0,MainScreen_Width , MainScreen_Height)];
    //m_tableView_peripheral.backgroundColor = [UIColor lightGrayColor];
    
    m_tableView_peripheral.tableFooterView = [[UIView alloc] initWithFrame:CGRectZero];
    
    m_tableView_peripheral.delegate = self;
    m_tableView_peripheral.dataSource = self;
    [self.view addSubview:m_tableView_peripheral];
    
    
    //[self setupRefreshControl];

    refreshControl = [[UIRefreshControl alloc] init];
    refreshControl.backgroundColor = [UIColor purpleColor];
    refreshControl.tintColor = [UIColor whiteColor];
    [refreshControl addTarget:self
                       action:@selector(scanPeripheralResult:)
                  forControlEvents:UIControlEventValueChanged];
    [m_tableView_peripheral addSubview:refreshControl];
    //[self numberOfSectionsInTableView:m_tableView_peripheral];
}

- (void)containingScrollViewDidEndDragging:(UIScrollView *)containingScrollView
{
    CGFloat minOffsetToTriggerRefresh = 50.0f;
    if (containingScrollView.contentOffset.y <= -minOffsetToTriggerRefresh) {
        [self scanPeripheralResult:nil];
    }
}

-(void)viewDidAppear:(BOOL)animated
{
    if ([Commom sharedInstance].currentPeripheral!=nil) {
        if ([Commom sharedInstance].currentPeripheral.state == CBPeripheralStateConnected) {
            [m_bleManger.m_manger cancelPeripheralConnection:[Commom sharedInstance].currentPeripheral];
        }
    }
}

-(void)viewWillAppear:(BOOL)animated
{
    m_bleManger = [BLEmanager shareInstance];
    m_bleManger.mange_delegate = self;
}
-(void)viewWillDisappear:(BOOL)animated
{
   m_bleManger.mange_delegate = nil;
}
-(void)scanPeripheralResult:(id)sender
{
    
    NSArray *services = [[NSArray alloc]init];
    
    [m_bleManger.m_manger scanForPeripheralsWithServices:nil options:@{ CBCentralManagerScanOptionAllowDuplicatesKey : @YES,CBCentralManagerScanOptionSolicitedServiceUUIDsKey : services }];
    m_timer_threesec=[NSTimer scheduledTimerWithTimeInterval:3.0 target:self selector:@selector(scanresult) userInfo:nil repeats:YES];

}


-(void)scanresult
{
    NSLog(@"V");
    [m_tableView_peripheral reloadData];
    [refreshControl endRefreshing];
    
  
    
    
}
- (CGFloat)tableView:(UITableView *)tableView heightForRowAtIndexPath:(NSIndexPath *)indexPath;
{
    return 100;
}
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section;

{
    UILabel *messageLabel = [[UILabel alloc] initWithFrame:CGRectMake(0, 0, self.view.bounds.size.width, self.view.bounds.size.height)];
    if ([m_bleManger.m_array_peripheral count] == 0) {
        messageLabel = [[UILabel alloc] initWithFrame:CGRectMake(0, 0, self.view.bounds.size.width, self.view.bounds.size.height)];
        
        messageLabel.text = @"Pull down to scan!";
        messageLabel.textColor = [UIColor blackColor];
        messageLabel.numberOfLines = 0;
        messageLabel.textAlignment = NSTextAlignmentCenter;
        messageLabel.font = [UIFont fontWithName:@"Courier" size:15];
        [messageLabel sizeToFit];
        
        m_tableView_peripheral.backgroundView = messageLabel;
        m_tableView_peripheral.separatorStyle = UITableViewCellSeparatorStyleNone;
    } else {
        messageLabel.text = @"";
        messageLabel.textColor = [UIColor blackColor];
        messageLabel.numberOfLines = 0;
        messageLabel.textAlignment = NSTextAlignmentCenter;
        messageLabel.font = [UIFont fontWithName:@"Courier" size:15];
        [messageLabel sizeToFit];
        m_tableView_peripheral.backgroundView = messageLabel;
        m_tableView_peripheral.separatorStyle = UITableViewCellSeparatorStyleSingleLine;
    }
    return [m_bleManger.m_array_peripheral count];
}

-(void)tableView:(UITableView *)tableView willDisplayCell:(UITableViewCell *)cell forRowAtIndexPath:(NSIndexPath *)indexPath{
    
    [cell setSeparatorInset:UIEdgeInsetsZero];
}

UILabel *label_NUM;
UILabel *label_LAST_REC;
UILabel *label_PWR;
UILabel *label_RSSI;
int cnt = 0;

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath;
{
    m_tableView_peripheral.separatorColor = [UIColor grayColor];
    NSString *cellIden = [NSString stringWithFormat:@"%ld%ld",(long)indexPath.section,(long)indexPath.row];
    UITableViewCell *mycell = [tableView dequeueReusableCellWithIdentifier:cellIden];
    
    
    if (!mycell) {
        
        mycell  = [[UITableViewCell alloc]initWithStyle:UITableViewCellStyleDefault reuseIdentifier:cellIden];
        
        UIImage *powerBladeImg = [UIImage imageNamed:@"powerblade.png"];
        UIImage * scaledImage =
        [UIImage imageWithCGImage:[powerBladeImg CGImage]
                            scale:(powerBladeImg.scale * 6)
                      orientation:(powerBladeImg.imageOrientation)];
        UIImageView * powerBladeImgView = [[UIImageView alloc] initWithImage:scaledImage];
        mycell.imageView.image = scaledImage;
        
        //[powerBladeImgView setFrame:CGRectMake(mycell.frame.origin.x,mycell.frame.origin.y, mycell.frame.size.height, mycell.frame.size.height)];
        //[mycell.contentView addSubview:powerBladeImgView];
    }
    
    NSString * last_time = label_LAST_REC.text;
    for (UIView *subView in mycell.contentView.subviews) {
        [subView removeFromSuperview];
    }
    
    label_NUM     = [[UILabel alloc] initWithFrame:CGRectMake(MainScreen_Width/4+15, 5, MainScreen_Width/2, 30)];
    label_NUM.textAlignment = NSTextAlignmentLeft;
    [mycell.contentView addSubview:label_NUM];
    
    label_LAST_REC = [[UILabel alloc] initWithFrame:CGRectMake(MainScreen_Width/4+15, 40, MainScreen_Width, 80)];
    label_LAST_REC.font = [UIFont systemFontOfSize:15.0];
    [mycell.contentView addSubview:label_LAST_REC];
    
    label_PWR = [[UILabel alloc] initWithFrame:CGRectMake(MainScreen_Width/4+15, 35, MainScreen_Width/3, 25)];
    label_PWR.font = [UIFont systemFontOfSize:15.0];
    [mycell.contentView addSubview:label_PWR];

    label_RSSI = [[UILabel alloc] initWithFrame:CGRectMake(MainScreen_Width/1.5+15, 35, MainScreen_Width/3, 25)];
    label_RSSI.font = [UIFont systemFontOfSize:15.0];
    [mycell.contentView addSubview:label_RSSI];
    

    if (m_bleManger.m_array_peripheral.count > 0) {
        NSLog(@"HIT 2");
        BlePeripheral *l_peri = [m_bleManger.m_array_peripheral objectAtIndex:indexPath.row];
        
        NSLog(@"hitting last peri %@", l_peri.last_time);

        NSLog([NSString stringWithFormat:@"l_peri tPower: %f",l_peri.m_tPower]);
        NSLog([NSString stringWithFormat:@"l_peri aPower: %f",l_peri.m_aPower]);
        
        label_NUM.text = [NSString stringWithFormat:@"PowerBlade #%d",l_peri.m_powerBladeID];
        label_RSSI.text = [NSString stringWithFormat:@"RSSI: %0.f", l_peri.m_rssi];
        
        
        
        label_PWR.text = [NSString stringWithFormat:@"Power: %.0f W",l_peri.m_tPower];
        
        NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
        [timeFormatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
        [timeFormatter setTimeZone:[NSTimeZone timeZoneWithName:@"GMT"]];
        NSString * newTime = [timeFormatter stringFromDate:[[NSDate alloc]init]];
                              
        if ([seq_map objectForKey:[NSNumber numberWithInteger:indexPath.row]] == nil) { //creating this
            [seq_map setObject:[NSNumber numberWithInt:l_peri.m_sequenceNum]
                        forKey:[NSNumber numberWithInteger:indexPath.row]];
                       NSDateFormatter *timeFormatter = [[NSDateFormatter alloc] init];
            NSLog(@"hitting a");
            
            label_LAST_REC.text = [NSString stringWithFormat:@"Last Rec: %@", newTime];
 
            
            [m_bleManger.m_array_peripheral replaceObjectAtIndex:indexPath.row withObject:l_peri];
            [seq_map_time setObject:newTime forKey:[NSNumber numberWithInt:l_peri.m_powerBladeID]];
            
            for (id key in seq_map_time) {
                NSLog(@"key: %@, value: %@ \n", key, [seq_map_time objectForKey:key]);
            }
            
            l_peri.last_time = newTime;
            [m_bleManger.m_array_peripheral replaceObjectAtIndex:indexPath.row withObject:l_peri];
        } else {
            NSLog(@"hitting b");

            NSString * lastSeqNum = [NSString stringWithFormat:@"%@", [seq_map objectForKey:[NSNumber numberWithInteger:indexPath.row]]];
            NSString * curSeqNum = [NSString stringWithFormat:@"%ld", (long)l_peri.m_sequenceNum];
            NSLog(@"LAST SEQ NUM: %@", lastSeqNum);
            NSLog(@"CUR SEQ NUM: %@", curSeqNum);
            if ([curSeqNum isEqualToString:lastSeqNum]) {
                NSLog(@"hitting c");
                NSLog(@"hitting LAST TIME %@", l_peri.last_time);
                NSDateFormatter *formatter = [[NSDateFormatter alloc] init];
                [formatter setDateFormat:@"MM/dd/yyyy HH:mm:ss"];
                NSDate *date2 = [formatter dateFromString:newTime];
                
                NSLog(@"hitting time %@", date2);
                
                NSNumberFormatter *f = [[NSNumberFormatter alloc] init];
                f.numberStyle = NSNumberFormatterDecimalStyle;
                NSNumber *myNumber = [NSNumber numberWithInt:l_peri.m_powerBladeID];
                NSLog(@"TIME %@", [seq_map_time objectForKey:myNumber]);
                NSDate *date1= [formatter dateFromString:[seq_map_time objectForKey:myNumber]];
                NSLog(@"hitting time %@", date1);
                NSTimeInterval distanceBetweenDates = [date2 timeIntervalSinceDate:date1];
        
                
                NSLog(@"hitting interval %f", distanceBetweenDates);
                double secondsInMinute = 60;
                NSInteger secondsBetweenDates = distanceBetweenDates / secondsInMinute;
                
                NSLog(@"hitting seconds %ld", (long)secondsBetweenDates);

                label_LAST_REC.text = [NSString stringWithFormat:@"Last Rec: %@", [seq_map_time objectForKey:myNumber]];

                
            } else {
                NSLog(@"hitting d");
                label_LAST_REC.text = [NSString stringWithFormat:@"Last Rec: %@", newTime];
                l_peri.last_time = newTime;
                [m_bleManger.m_array_peripheral replaceObjectAtIndex:indexPath.row withObject:l_peri];
                
                for (id key in seq_map_time) {
                    NSLog(@"key: %@, value: %@ \n", key, [seq_map_time objectForKey:key]);
                }

            }
        }
    }
    return mycell;
}

 
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath;
{
    [m_timer_threesec invalidate];
     BlePeripheral *l_peri = [m_bleManger.m_array_peripheral objectAtIndex:indexPath.row];
    [m_bleManger.m_manger connectPeripheral:l_peri.m_peripheral options:nil];
    m_current_peripheralInfo = l_peri;
    [[Commom sharedInstance]setCurrentPeripheral:l_peri.m_peripheral];
    [m_bleManger.m_manger stopScan];
     m_timer_Connect = [NSTimer scheduledTimerWithTimeInterval:10.0 target:self selector:@selector(connectPeripheralFailed) userInfo:nil repeats:NO];
}

#pragma mark_BLEMangerDelegate
-(void)bleMangerConnectedPeripheral :(BOOL)isConnect;
{
    if (isConnect == YES) {
        showConnectingHUD.hidden = YES;
        [m_timer_Connect invalidate];

        CharacteristicInfoViewController *characterVC = [[CharacteristicInfoViewController alloc]init];
        characterVC.curBLE = m_current_peripheralInfo;
        [self.navigationController pushViewController:characterVC animated:YES];
        [m_bleManger.m_manger stopScan];
    }
}
-(void)bleMangerReceiveDataPeripheralData :(NSData *)data from_Characteristic :(CBCharacteristic *)curCharacteristic;
{
}
-(void)bleMangerDisconnectedPeripheral :(CBPeripheral *)_peripheral;
{
    if ([_peripheral isEqual:[Commom sharedInstance].currentPeripheral]) {
        NSLog(@ "Disconnected");
        [showConnectingHUD hide:YES];
        [self scanPeripheralResult:nil];
    }
}

#pragma mark_NSTimer Function
-(void)connectPeripheralFailed
{
    [self scanPeripheralResult:nil];
}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning];
}

@end
