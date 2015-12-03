//
//  SecViewController.h
//  BLE4.0Demo
//
//  Created by kakaxi on 15/4/17.
//  Copyright (c) 2015年 kakaxi Email:631965569@qq.com  . All rights reserved.
//

#import <UIKit/UIKit.h>

@interface SecViewController : UIViewController
- (IBAction)readBattery:(id)sender;
- (IBAction)readPeripheralInfo:(id)sender;
@property (weak, nonatomic) IBOutlet UILabel *currentBattery;
@property (weak, nonatomic) IBOutlet UITextView *textView_PeripheralInfo;

@end
