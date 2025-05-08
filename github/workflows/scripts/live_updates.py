import sys
import os
import time
import random

# إضافة المجلد الجذر إلى مسار البحث ليتمكن من استيراد الوحدات المشتركة
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpl_api import get_current_gameweek, get_live_match_data, detect_live_events
from twitter_api import post_tweet
from formatters import format_live_match_update, format_live_event_tweet
from config import EVENT_TYPES

def main():
    """
    نقطة الدخول الرئيسية لتحديثات المباريات المباشرة
    """
    print("بدء معالجة تحديثات المباريات المباشرة...")
    
    # الحصول على الجولة الحالية
    current_gw = get_current_gameweek()
    if not current_gw:
        print("لا يمكن تحديد الجولة الحالية")
        return
    
    # التحقق من الأحداث المباشرة
    new_events = detect_live_events(current_gw)
    
    if new_events:
        print(f"تم اكتشاف {len(new_events)} أحداث جديدة!")
        
        # نشر تغريدة لكل حدث
        for event in new_events:
            tweet_text = format_live_event_tweet(event)
            if tweet_text:
                print(f"نشر تحديث: {tweet_text}")
                status = post_tweet(tweet_text)
                if status:
                    print(f"تم نشر تحديث للحدث: {event['event_type']} لـ {event['player_name']}")
                else:
                    print(f"فشل في نشر التحديث للحدث: {event['event_type']} لـ {event['player_name']}")
                
                # انتظار قصير وعشوائي بين التغريدات (1-3 ثواني)
                time.sleep(random.uniform(1, 3))
    else:
        print("لا توجد أحداث جديدة للنشر")
    
    # الحصول على بيانات المباريات المباشرة للتحديثات المنتظمة
    live_data = get_live_match_data(current_gw)
    if not live_data:
        print("لا توجد بيانات مباشرة متاحة")
        return
    
    # معالجة المباريات الجارية وتنسيقها للنشر (التحديثات المنتظمة كل 15 دقيقة)
    active_matches = extract_active_matches(live_data)
    
    if not active_matches:
        print("لا توجد مباريات نشطة حالياً")
        return
    
    # التحقق مما إذا كانت هناك تحديثات دورية للمباريات
    current_minute = int(time.time() / 60)
    if current_minute % 15 == 0:  # كل 15 دقيقة فقط
        for match in active_matches:
            is_final = match.get('status') == 'FT'
            tweet_text = format_live_match_update(match, is_final)
            if tweet_text:
                status = post_tweet(tweet_text)
                if status:
                    print(f"تم نشر تحديث دوري لمباراة {match.get('home_team', '')} vs {match.get('away_team', '')}")
                
                # انتظار بين التغريدات
                time.sleep(5)

def extract_active_matches(live_data):
    """
    استخراج المباريات النشطة من بيانات FPL
    """
    active_matches = []
    
    # نستخدم هنا API fixtures مع تصفية المباريات الحالية
    if 'fixtures' in live_data:
        for fixture in live_data.get('fixtures', []):
            # نتحقق إذا كانت المباراة جارية
            if fixture.get('started', False) and not fixture.get('finished', False):
                # استخراج معلومات الفريقين
                team_h = fixture.get('team_h', 0)
                team_a = fixture.get('team_a', 0)
                
                # إعداد بيانات المباراة
                match_data = {
                    'fixture_id': fixture.get('id'),
                    'home_team': get_team_name(team_h),
                    'away_team': get_team_name(team_a),
                    'home_score': fixture.get('team_h_score', 0),
                    'away_score': fixture.get('team_a_score', 0),
                    'status': get_match_status(fixture),
                    'minutes': fixture.get('minutes', 0),
                }
                
                active_matches.append(match_data)
    
    return active_matches

def get_team_name(team_id):
    """
    الحصول على اسم الفريق من الهوية
    """
    from config import TEAM_CODES
    return TEAM_CODES.get(team_id, f'TEAM{team_id}')

def get_match_status(fixture):
    """
    الحصول على حالة المباراة
    """
    if fixture.get('finished', False):
        return 'FT'
    elif fixture.get('started', False):
        minutes = fixture.get('minutes', 0)
        return f"{minutes}'"
    else:
        return 'PENDING'

if __name__ == "__main__":
    main()
          
