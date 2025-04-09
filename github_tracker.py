import os
import time
from datetime import datetime, timedelta
from github import Github, RateLimitExceededException
from logger import logger

class GitHubTracker:
    def __init__(self):
        """
        Инициализирует трекер GitHub для отслеживания активности в криптопроектах
        """
        # Токен API GitHub (необходим для увеличения лимита запросов)
        # Без токена лимит - 60 запросов в час, с токеном - 5000 запросов в час
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        
        # Инициализация клиента GitHub API
        if self.github_token:
            self.github = Github(self.github_token)
            logger.info("Используется аутентификация для доступа к GitHub API")
        else:
            self.github = Github()
            logger.warning("Используется анонимный доступ к GitHub API. Установите переменную окружения GITHUB_TOKEN для увеличения лимита запросов.")

        # Список отслеживаемых репозиториев
        self.repos = [
            {"owner": "bitcoin", "repo": "bitcoin", "name": "Bitcoin Core", "symbol": "BTC", "icon": "₿"},
            {"owner": "ethereum", "repo": "go-ethereum", "name": "Ethereum (Go)", "symbol": "ETH", "icon": "Ξ"},
            {"owner": "solana-labs", "repo": "solana", "name": "Solana", "symbol": "SOL", "icon": "◎"},
            {"owner": "cardano-foundation", "repo": "cardano-node", "name": "Cardano Node", "symbol": "ADA", "icon": "₳"},
            {"owner": "dogecoin", "repo": "dogecoin", "name": "Dogecoin", "symbol": "DOGE", "icon": "Ð"},
        ]
        
        # Кеш для хранения данных о репозиториях
        self.cache = {}
        self.cache_expiry = 3600  # Время жизни кеша в секундах (1 час)
        
        # Интервал между запросами для соблюдения ограничений API
        self.request_interval = 1.0  # секунды
        self.last_request_time = None

    def _respect_rate_limit(self):
        """
        Соблюдает минимальный интервал между запросами к API GitHub
        для избежания блокировки
        """
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_interval:
                sleep_time = self.request_interval - elapsed
                logger.info(f"Ожидание {sleep_time:.2f} сек. перед следующим запросом к GitHub API...")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_repo_activity(self, owner, repo):
        """
        Получает данные об активности в репозитории
        
        Args:
            owner (str): Владелец репозитория (пользователь или организация)
            repo (str): Название репозитория
            
        Returns:
            dict: Данные об активности репозитория или None в случае ошибки
        """
        cache_key = f"{owner}/{repo}"
        
        # Проверяем наличие данных в кеше
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # Проверяем, не истек ли срок действия кеша
            if time.time() - cache_entry['timestamp'] < self.cache_expiry:
                logger.info(f"Используем кешированные данные для репозитория {owner}/{repo}")
                return cache_entry['data']
        
        try:
            # Соблюдаем ограничения API
            self._respect_rate_limit()
            
            # Получаем репозиторий
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            # Получаем общую информацию о репозитории
            stars = repository.stargazers_count
            forks = repository.forks_count
            open_issues = repository.open_issues_count
            
            # Получаем дату последнего обновления
            last_update = repository.updated_at
            
            # Получаем последние коммиты
            self._respect_rate_limit()
            recent_commits = []
            try:
                commits = repository.get_commits()
                
                for commit in list(commits)[:10]:  # Ограничиваем до 10 последних коммитов
                    self._respect_rate_limit()
                    recent_commits.append({
                        'sha': commit.sha[:7],
                        'message': commit.commit.message.split('\n')[0][:50],  # Первая строка сообщения, обрезанная до 50 символов
                        'author': commit.commit.author.name,
                        'date': commit.commit.author.date.strftime('%Y-%m-%d'),
                    })
            except Exception as e:
                logger.error(f"Ошибка при получении коммитов для {owner}/{repo}: {str(e)}")
            
            # Получаем активность за последний месяц
            one_month_ago = datetime.now() - timedelta(days=30)
            
            self._respect_rate_limit()
            monthly_commits = 0
            try:
                # Получаем коммиты за последний месяц
                monthly_commits_iterator = repository.get_commits(since=one_month_ago)
                # Вместо использования totalCount, который может вызвать ошибку,
                # используем безопасный подсчет первых 100 коммитов
                monthly_commits = len(list(monthly_commits_iterator[:100]))
                # Если количество равно 100, возможно есть еще коммиты, но мы ограничиваем запрос
                if monthly_commits == 100:
                    monthly_commits = f"{monthly_commits}+"
            except Exception as e:
                logger.error(f"Ошибка при подсчете коммитов за месяц для {owner}/{repo}: {str(e)}")
            
            # Получаем информацию о последних релизах
            self._respect_rate_limit()
            recent_releases = []
            try:
                releases = repository.get_releases()
                
                for release in list(releases)[:3]:  # Ограничиваем до 3 последних релизов
                    self._respect_rate_limit()
                    recent_releases.append({
                        'tag': release.tag_name,
                        'name': release.title,
                        'date': release.created_at.strftime('%Y-%m-%d'),
                    })
            except Exception as e:
                logger.error(f"Ошибка при получении релизов для {owner}/{repo}: {str(e)}")
            
            # Собираем все данные в один словарь
            repo_data = {
                'name': repository.name,
                'full_name': repository.full_name,
                'description': repository.description,
                'stars': stars,
                'forks': forks,
                'open_issues': open_issues,
                'last_update': last_update.strftime('%Y-%m-%d'),
                'monthly_commits': monthly_commits,
                'recent_commits': recent_commits,
                'recent_releases': recent_releases,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Сохраняем результаты в кеш
            self.cache[cache_key] = {
                'timestamp': time.time(),
                'data': repo_data
            }
            
            return repo_data
            
        except RateLimitExceededException:
            logger.error(f"Превышен лимит запросов к GitHub API. Попробуйте позже или используйте токен.")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных о репозитории {owner}/{repo}: {str(e)}")
            return None
    
    def get_all_repos_activity(self):
        """
        Получает данные об активности для всех отслеживаемых репозиториев
        
        Returns:
            dict: Данные об активности всех репозиториев
        """
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'repositories': []
        }
        
        for repo_info in self.repos:
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            logger.info(f"Получение данных о репозитории {owner}/{repo}...")
            repo_data = self.get_repo_activity(owner, repo)
            
            if repo_data:
                # Добавляем дополнительную информацию из нашего списка отслеживаемых репозиториев
                repo_data['display_name'] = repo_info.get('name', repo_data['name'])
                repo_data['symbol'] = repo_info.get('symbol', '')
                repo_data['icon'] = repo_info.get('icon', '')
                
                results['repositories'].append(repo_data)
        
        # Сортируем репозитории по количеству звезд (от большего к меньшему)
        results['repositories'] = sorted(
            results['repositories'],
            key=lambda x: x.get('stars', 0),
            reverse=True
        )
        
        return results
    
    def format_activity_message(self, activity_data):
        """
        Форматирует данные об активности репозиториев в сообщение для Telegram
        
        Args:
            activity_data (dict): Данные об активности репозиториев
            
        Returns:
            str: Отформатированное сообщение для Telegram
        """
        if not activity_data or 'repositories' not in activity_data or not activity_data['repositories']:
            return "❌ Не удалось получить данные об активности GitHub."
        
        # Форматируем сообщение с заголовком
        message = f"🛠️ *GitHub Crypto Projects Activity*\n\n"
        
        # Добавляем сводку по всем репозиториям
        message += "*⭐ STARS LEADERBOARD:*\n"
        
        for repo in activity_data['repositories'][:5]:  # Топ-5 по звездам
            icon = repo.get('icon', '')
            symbol = repo.get('symbol', '')
            display_name = repo.get('display_name', repo['name'])
            stars = repo.get('stars', 0)
            
            message += f"{icon} *{display_name}* ({symbol}): {stars:,} ⭐\n"
        
        message += "\n*🔥 MONTHLY COMMITS:*\n"
        
        # Создаем функцию для безопасной сортировки
        def get_commits_for_sorting(repo):
            monthly_commits = repo.get('monthly_commits', 0)
            if isinstance(monthly_commits, str) and monthly_commits.endswith('+'):
                # Если значение вида "100+", берем число без "+"
                return int(monthly_commits[:-1])
            return monthly_commits if isinstance(monthly_commits, int) else 0
            
        # Сортируем по количеству коммитов за месяц
        sorted_by_commits = sorted(
            activity_data['repositories'],
            key=get_commits_for_sorting,
            reverse=True
        )
        
        for repo in sorted_by_commits[:5]:  # Топ-5 по коммитам за месяц
            icon = repo.get('icon', '')
            symbol = repo.get('symbol', '')
            display_name = repo.get('display_name', repo['name'])
            monthly_commits = repo.get('monthly_commits', 0)
            
            message += f"{icon} *{display_name}* ({symbol}): {monthly_commits} коммитов за 30 дней\n"
        
        # Добавляем детальную информацию о последних релизах для топ-3 проектов
        message += "\n*🚀 RECENT RELEASES:*\n"
        
        for repo in activity_data['repositories'][:3]:  # Топ-3 по звездам
            icon = repo.get('icon', '')
            display_name = repo.get('display_name', repo['name'])
            
            message += f"{icon} *{display_name}*: "
            
            recent_releases = repo.get('recent_releases', [])
            if recent_releases:
                release = recent_releases[0]  # Самый последний релиз
                message += f"`{release['tag']}` ({release['date']})\n"
            else:
                message += "Нет данных о релизах\n"
        
        # Добавляем информацию о последних коммитах для самого активного проекта
        most_active_repo = sorted_by_commits[0] if sorted_by_commits else None
        
        if most_active_repo:
            icon = most_active_repo.get('icon', '')
            display_name = most_active_repo.get('display_name', most_active_repo['name'])
            
            message += f"\n*📝 LATEST COMMITS FOR {display_name}:*\n"
            
            recent_commits = most_active_repo.get('recent_commits', [])
            for i, commit in enumerate(recent_commits[:3]):  # Показываем только 3 последних коммита
                message += f"{i+1}. `{commit['sha']}` {commit['message'][:30]}... ({commit['date']})\n"
        
        # Добавляем информацию о времени получения данных
        timestamp = activity_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        message += f"\n_Данные получены: {timestamp}_"
        
        return message
        
    def format_compact_message(self, activity_data):
        """
        Форматирует компактную версию данных об активности для Telegram
        
        Args:
            activity_data (dict): Данные об активности репозиториев
            
        Returns:
            str: Компактное сообщение для Telegram
        """
        if not activity_data or 'repositories' not in activity_data or not activity_data['repositories']:
            return "❌ Не удалось получить данные об активности GitHub."
        
        # Форматируем компактное сообщение
        message = f"🛠️ *GitHub Pulse*\n\n"
        
        # Сортируем по количеству коммитов за месяц
        sorted_by_commits = sorted(
            activity_data['repositories'],
            key=lambda x: x.get('monthly_commits', 0),
            reverse=True
        )
        
        # Создаем строку с активностью репозиториев
        activity_line = ""
        for repo in sorted_by_commits:
            icon = repo.get('icon', '')
            symbol = repo.get('symbol', '')
            monthly_commits = repo.get('monthly_commits', 0)
            
            # Определяем индикатор активности
            if monthly_commits > 100:
                activity_indicator = "🔥"  # Высокая активность
            elif monthly_commits > 50:
                activity_indicator = "⚡"  # Средняя активность
            elif monthly_commits > 10:
                activity_indicator = "✓"   # Низкая активность
            else:
                activity_indicator = "❄️"  # Очень низкая активность
            
            activity_line += f"{icon}{activity_indicator}{monthly_commits} "
            
        message += f"*Commits (30d):* {activity_line.strip()}\n\n"
        
        # Добавляем строку со звездами
        stars_line = ""
        for repo in activity_data['repositories']:
            icon = repo.get('icon', '')
            stars = repo.get('stars', 0)
            
            # Форматируем число звезд
            if stars >= 10000:
                stars_formatted = f"{stars/1000:.1f}k"
            else:
                stars_formatted = f"{stars}"
                
            stars_line += f"{icon}⭐{stars_formatted} "
            
        message += f"*Stars:* {stars_line.strip()}\n"
        
        # Добавляем строку с релизами
        release_line = ""
        for repo in activity_data['repositories']:
            icon = repo.get('icon', '')
            recent_releases = repo.get('recent_releases', [])
            
            if recent_releases:
                release = recent_releases[0]  # Самый последний релиз
                release_line += f"{icon}`{release['tag']}` "
            else:
                release_line += f"{icon}- "
                
        message += f"*Latest versions:* {release_line.strip()}"
        
        return message