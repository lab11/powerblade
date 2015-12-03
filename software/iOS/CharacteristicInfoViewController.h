
#import <UIKit/UIKit.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import "BlePeripheral.h"
@interface CharacteristicInfoViewController : UIViewController


@property(nonatomic,retain)CBCharacteristic *curCharacteristic;
@property(nonatomic,retain) BlePeripheral *curBLE;

@end
