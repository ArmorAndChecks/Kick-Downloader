# kickapi/channel_data.py
from kickapi.clip_data import ClipData 
from kickapi.video_data import VideoData
from kickapi.leaderboard_data import LeaderboardData

class ChannelData():
    def __init__(self, data, api):
        self._api = api
        self.id = data.get("id")
        self.user_id = data.get("user_id")
        self.username = data.get("slug")
        self.playback = data.get("playback_url")
        self.is_banned = data.get("is_banned", False)
        self.subscriber_count = data.get("subscriber_count", 0)
        self.followers = data.get("followersCount", 0)
        self.livestream = data.get("livestream")
        
        user = data.get("user", {})
        self.bio = user.get("bio")
        self.avatar = user.get("profile_pic")
        self.verified = data.get("verified", False) or user.get("verified", False)
        
        # Socials
        self.twitter = data.get("twitter")
        self.facebook = data.get("facebook")
        self.instagram = data.get("instagram")
        self.youtube = data.get("youtube")
        self.discord = data.get("discord")
        self.tiktok = data.get("tiktok")

    @property
    def videos(self):
        url = f"https://kick.com/api/v2/channels/{self.username}/videos"
        response = self._api.session.get(url, headers=self._api.headers)
        try:
            data = response.json()
            return [VideoData(video) for video in data]
        except ValueError:
            print("Failed to parse clips JSON.")
            return []

    @property
    def clips(self):
        url = f"https://kick.com/api/v2/channels/{self.username}/clips"
        response = self._api.session.get(url, headers=self._api.headers)
        try:
            data = response.json().get("clips", [])
            return [ClipData(clip) for clip in data]
        except ValueError:
            print("Failed to parse clips JSON.")
            return []
        
    @property
    def leaderboards(self):
        url = f"https://kick.com/api/v2/channels/{self.username}/leaderboards"
        response = self._api.session.get(url, headers=self._api.headers)
        try:
            data = response.json()
            return LeaderboardData(data)
        except ValueError:
            print("Failed to parse clips JSON.")
            return LeaderboardData({})
