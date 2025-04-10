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
	x = 1; y = 1; p = 8, q = 8; //x,y:���a��l�Ʈy�СAp,q:�X�f�y��
	cout << "�ϥΤW�U���k����O�A�N@����X�B\n";
	for (int i = 0; i <= 9; i++) cout << map[i] << endl;

	while (map[p][q] != '@')
	{
		sokoban(map, &x, &y); //���s�]�w�a�Ϯy�� 
		system("cls"); //�M���ù��¦a��
		cout << "�ϥΤW�U���k����O�A�N@����X�B\n";
		for (int i = 0; i <= 9; i++) cout << map[i] << endl;
	}
	cout << "���߹L��!\n";
	system("pause");
}

void sokoban(char a[][15], int* x, int* y)
{
	char key;
	key = _getch();
	switch (key)
	{
	case 72:
		//�����V�W���ʬO�_���I�쪫�� 
		if (a[*x - 1][*y] == '@') //�V�W���ʦ��I�쪫��
		{
			if (a[*x - 2][*y] != '+' && a[*x - 2][*y] != '-' && a[*x - 2][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)--;
				a[*x][*y] = 'O';
				a[*x - 1][*y] = '@';
			}
		}
		else //�V�W���ʵL�I�쪫�� 
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
		if (a[*x + 1][*y] == '@') //�V�W���ʦ��I�쪫��
		{
			if (a[*x + 2][*y] != '+' && a[*x + 2][*y] != '-' && a[*x + 2][*y] != '|')
			{
				a[*x][*y] = ' ';
				(*x)++;
				a[*x][*y] = 'O';
				a[*x + 1][*y] = '@';
			}
		}
		else //�V�W���ʵL�I�쪫�� 
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
		if (a[*x][*y - 1] == '@') //�V�W���ʦ��I�쪫��
		{
			if (a[*x][*y - 2] != '+' && a[*x][*y - 2] != '-' && a[*x][*y - 2] != '|')
			{
				a[*x][*y] = ' ';
				(*y)--;
				a[*x][*y] = 'O';
				a[*x][*y - 1] = '@';
			}
		}
		else //�V�W���ʵL�I�쪫�� 
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
		if (a[*x][*y + 1] == '@') //�V�W���ʦ��I�쪫��
		{
			if (a[*x][*y + 2] != '+' && a[*x][*y + 2] != '-' && a[*x][*y + 2] != '|')
			{
				a[*x][*y] = ' ';
				(*y)++;
				a[*x][*y] = 'O';
				a[*x][*y + 1] = '@';
			}
		}
		else //�V�W���ʵL�I�쪫�� 
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


