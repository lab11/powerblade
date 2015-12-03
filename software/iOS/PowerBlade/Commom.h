

#import <Foundation/Foundation.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import "Header.h"
@interface Commom : NSObject
AS_SINGLETON(Commom);

@property(nonatomic,copy)CBPeripheral *currentPeripheral;
@property(nonatomic,copy)NSMutableArray *bleObjs;


@end
