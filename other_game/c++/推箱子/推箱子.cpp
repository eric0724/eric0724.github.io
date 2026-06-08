#include<iostream>
#include<cstdlib>
#include<conio.h>
using namespace std;
void sokoban(char map[][15], int*, int*);
int main()
{
	char map[15][15] = { "+--------+",
						"|O       |",
						"| @+---  |",
						"|        |",
						"|-- ---  |",
						"|   |    |",
						"|        |",
						"| | -----|",
						"|       X|",
						"+--------+" };
	int x, y, p, q;
	x = 1; y = 1; p = 8, q = 8; //x,y:玩家初始化座標，p,q:出口座標
	cout << "使用上下左右移動O，將@推到X處\n";
	for (int i = 0; i <= 9; i++) cout << map[i] << endl;

	while (map[p][q] != '@')
	{
		sokoban(map, &x, &y); //重新設定地圖座標 
		system("cls"); //清除螢幕舊地圖
		cout << "使用上下左右移動O，將@推到X處\n";
		for (int i = 0; i <= 9; i++) cout << map[i] << endl;
	}
	cout << "恭喜過關!\n";
	system("pause");
}

void sokoban(char a[][15], int* x, int* y)
{
	char key;
	key = _getch();
	switch (key)
	{
	case 72:
		//偵測向上移動是否有碰到物體 
		if (a[*x - 1][*y] == '@') //向上移動有碰到物體
		{
			if (a[*x - 2][*y] != '+' && a[*x - 2][*y] != '-' && a[*x - 2][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)--;
				a[*x][*y] = 'O';
				a[*x - 1][*y] = '@';
			}
		}
		else //向上移動無碰到物體 
		{
			if (a[*x - 1][*y] != '+' && a[*x - 1][*y] != '-' && a[*x - 1][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)--;
				a[*x][*y] = 'O';
			}
		}
		break;

	case 80:
		if (a[*x + 1][*y] == '@') //向上移動有碰到物體
		{
			if (a[*x + 2][*y] != '+' && a[*x + 2][*y] != '-' && a[*x + 2][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)++;
				a[*x][*y] = 'O';
				a[*x + 1][*y] = '@';
			}
		}
		else //向上移動無碰到物體 
		{
			if (a[*x + 1][*y] != '+' && a[*x + 1][*y] != '-' && a[*x + 1][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)++;
				a[*x][*y] = 'O';
			}
		}
		break;

	case 75:
		if (a[*x][*y - 1] == '@') //向上移動有碰到物體
		{
			if (a[*x][*y - 2] != '+' && a[*x][*y - 2] != '-' && a[*x][*y - 2] != '|')
			{
				a[*x][*y] = ' ';
				(*y)--;
				a[*x][*y] = 'O';
				a[*x][*y - 1] = '@';
			}
		}
		else //向上移動無碰到物體 
		{
			if (a[*x][*y - 1] != '+' && a[*x][*y - 1] != '-' && a[*x][*y - 1] != '|')
			{
				a[*x][*y] = ' ';
				(*y)--;
				a[*x][*y] = 'O';
			}
		}
		break;

	case 77:
		if (a[*x][*y + 1] == '@') //向上移動有碰到物體
		{
			if (a[*x][*y + 2] != '+' && a[*x][*y + 2] != '-' && a[*x][*y + 2] != '|')
			{
				a[*x][*y] = ' ';
				(*y)++;
				a[*x][*y] = 'O';
				a[*x][*y + 1] = '@';
			}
		}
		else //向上移動無碰到物體 
		{
			if (a[*x][*y + 1] != '+' && a[*x][*y + 1] != '-' && a[*x][*y + 1] != '|')
			{
				a[*x][*y] = ' ';
				(*y)++;
				a[*x][*y] = 'O';
			}
		}
		break;
	}

}





int onex = 1, oney = 0, twox = 5, twoy = 0, threex = 9, threey = 0;
	int fourx = 1, foury = 2, fivex = 5, fivey = 2, sixx = 9, sixy = 2;
	int sevenx = 1, seveny = 4, eightx = 5, eighty = 4, ninex = 9, niney = 4;


