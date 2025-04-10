#include <iostream>
#include <ctime>
#include <cstdlib>
#include <conio.h> 
#include <Windows.h>
using namespace std;

int play = 1;
int s = 9 ,r = 1,ba = 8,ms = 0,ss=0,as=0,H=3;
void sokoban(char map[][50], int*, int*);
void b(char map[][50], int*, int*);

// 清除控制台視窗的函數 用gpt找的
void ClearConsole()
{
    HANDLE hStdOut = GetStdHandle(STD_OUTPUT_HANDLE);
    COORD coord = {0, 0};
    DWORD count;
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    GetConsoleScreenBufferInfo(hStdOut, &csbi);
    FillConsoleOutputCharacter(hStdOut, ' ', csbi.dwSize.X * csbi.dwSize.Y, coord, &count);
    SetConsoleCursorPosition(hStdOut, coord);
}

void b0(char b[][50], int* Xx, int* Xy)
{
    if (*Xy > 1 && b[*Xx][*Xy - 1] != '|' && b[*Xx][*Xy - 1] != '-')
    {
        b[*Xx][*Xy] = ' ';
        (*Xy)--;
		if (b[*Xx][*Xy] == 'Q')	(*Xy)--;
        b[*Xx][*Xy] = 'X';
    }
    else
    {
		r= (rand() % 20)+1;
        b[*Xx][*Xy] = ' ';
        (*Xx) = (rand() % 8) + 1;
        (*Xx) = 43;
        b[*Xx][*Xy] = 'X';
        as++;
    }
    if (b[*Xx][*Xy-1] == 'O')
        H--;
    if ( s < 20) Sleep(100-s*5); else Sleep(5);
}
void b1(char b[][50], int* Xx, int* Xy)
{
    for (int i = 43; i >= 1; i--) { if (b[ba][i] != 'O' )b[ba][i] = ' '; }
    if (*Xy > 1 && b[*Xx][*Xy - 1] != '|' && b[*Xx][*Xy - 1] != '-')
    {
        (*Xy)--;
        if (b[*Xx][*Xy] == 'Q')	(*Xy)--;
        b[*Xx][*Xy] = 'X';
    }
    else
    {
		r= (rand() % 20)+1;
		ba = (*Xx);
        (*Xx) = (rand() % 8) + 1;
        (*Xy) = 43;
        b[*Xx][*Xy] = 'X';
        as++;
    }
    if (b[*Xx][*Xy-1] == 'O')
        H--;
    if ( s < 20) Sleep(100-s*5); else Sleep(5);
}
void b2(char b[][50], int* Xx, int* Xy)
{
    if (*Xy > 1 && b[*Xx-1][*Xy - 5] != '|' && b[*Xx-1][*Xy - 5] != '-')
    {
    	b[*Xx][*Xy] = ' ';
        (*Xy)-=5;
        (*Xx)--;
        if (b[*Xx][*Xy] == 'Q')	(*Xy)--;
        b[*Xx][*Xy] = 'X';
    }
    else
    {
    	b[*Xx][*Xy] = ' ';
		r= (rand() % 20)+1;
        (*Xx) = (rand() % 8) + 1;
        (*Xy) = 43;
        b[*Xx][*Xy] = 'X';
        as++;
    }
    if (b[*Xx][*Xy-1] == 'O')
        H--;
    if ( s < 20) Sleep(100-s*4); else Sleep(50);
}
void b3(char b[][50], int* Xx, int* Xy)
{
    if (*Xy > 1 && b[*Xx+1][*Xy - 5] != '|' && b[*Xx+1][*Xy - 5] != '-')
    {
    	b[*Xx][*Xy] = ' ';
        (*Xy)-=5;
        (*Xx)++;
        if (b[*Xx][*Xy] == 'Q')	(*Xy)--;
        b[*Xx][*Xy] = 'X';
    }
    else
    {
    	b[*Xx][*Xy] = ' ';
		r= (rand() % 20)+1;
        (*Xx) = (rand() % 8) + 1;
        (*Xy) = 43;
        b[*Xx][*Xy] = 'X';
        as++;
    }
    if (b[*Xx][*Xy-1] == 'O')
        H--;
    if ( s < 20) Sleep(100-s*4); else Sleep(50);
}
void apple(char apple[][50], int* Ax, int* Ay)
{
	r= (rand() % 20)+1;
	apple[*Ax][*Ay] = ' ';
    (*Ax) = (rand() % 8) + 1;
    (*Ay) = (rand() % 43) + 1;
    apple[*Ax][*Ay] = 'Q';
    s++; 
}
void sokoban(char a[][50], int* Ox, int* Oy)
{
    if (_kbhit()) {    //在等待輸入時還能繼續跑(gpt)
        char key = _getch();    //在等待輸入時還能繼續跑(gpt)

        switch (key)
        {
        case 72: //上
            if (a[*Ox][*Oy + 1] == 'Q') {	ss+=10; }
			if (a[*Ox - 1][*Oy] == 'X') H--;
			else if (*Ox > 1 && a[*Ox - 1][*Oy] != '|' && a[*Ox - 1][*Oy] != '-' && a[*Ox - 1][*Oy] != '+')
            {
                a[*Ox][*Oy] = ' ';
                (*Ox)--;
                a[*Ox][*Oy] = 'O';
            }
            break;
        case 80: //下
        	if (a[*Ox][*Oy + 1] == 'Q') {	ss+=10; }
			if (a[*Ox + 1][*Oy] == 'X') H--;
            else if (*Ox < 8 && a[*Ox + 1][*Oy] != '|' && a[*Ox + 1][*Oy] != '-' && a[*Ox + 1][*Oy] != '+')
            {
                a[*Ox][*Oy] = ' ';
                (*Ox)++;
                a[*Ox][*Oy] = 'O';
            }
            break;
        case 75: //左
        	if (a[*Ox][*Oy + 1] == 'Q') {	ss+=10; }
			if ( a[*Ox][*Oy - 1] == 'X') H--;
            else if (*Oy > 1 && a[*Ox][*Oy - 1] != '|' && a[*Ox][*Oy - 1] != '-' && a[*Ox][*Oy - 1] != '+')
            {
                a[*Ox][*Oy] = ' ';
                (*Oy)--;
                a[*Ox][*Oy] = 'O';
            }
            break;
        case 77: //右
        	if (a[*Ox][*Oy + 1] == 'Q') {	ss+=10; }
			if (a[*Ox][*Oy + 1] == 'X') H--;
            else if (*Oy < 43 && a[*Ox][*Oy + 1] != '|' && a[*Ox][*Oy + 1] != '-' && a[*Ox][*Oy + 1] != '+')
            {
                a[*Ox][*Oy] = ' ';
                (*Oy)++;
                a[*Ox][*Oy] = 'O';
            }
            break;
        }
    }
}

int main()
{
    srand(time(0));

    char map[50][50] =
        {"+-------------------------------------------+",
         "|O                                          |",
         "|                                           |",
         "|                                           |",
         "|                                           |",
         "|                                           |",
         "|                                          X|",
         "|                                           |",
         "|                                           |",
         "+-------------------------------------------+"};

    int Ox = 1, Oy = 1, Xx = 6, Xy = 43,Ax=0,Ay=0;
    //  移動O的座標xy  移動X的座標pq 移動Q的座標ab
    for (int i = 0; i <= 9; i++)
        cout << map[i] << endl;
    while (play == 1)
    {
        sokoban(map, &Ox, &Oy);
        ClearConsole();
        if(s+ss>ms) ms = s+ss;
        cout <<"最高紀錄:"<< ms << endl;
        for (int i = H; i >  0; i--)	cout <<"O";
        cout <<endl;
        if(H <= 0)	play = 0;
        map[Ox][Oy] = 'O';
        for (int i = 0; i <= 9; i++)
            cout << map[i] << endl;
        cout <<"分數:"<< s<<"+"<<ss<< endl;
    	cout <<"請使用上下左右控制O不被X撞到"<< endl;
    	cout <<"並使分數達到100分以上"<< endl;
    	cout <<"可以控制O去吃Q來使自己加分"<< endl;
		if(r<10 || r%4 ==0)			{ b0(map, &Xx, &Xy); }
		else if(r >= 10 && r%4 ==1)	{ b1(map, &Xx, &Xy); } 
		else if(r >= 10 && r%4 ==2)	{ b2(map, &Xx, &Xy); } 
		else if(r >= 10 && r%4 ==3)	{ b3(map, &Xx, &Xy); }
		if(as > 2)	{ s++; as = 0; } 
		if(s % 10 == 0 && s != 0 )	apple(map, &Ax, &Ay); 
		if(play == 0){
			cout<<"如果要繼續請按1，否則按0"<<endl;
    		cin>>play;
    		if(play > 0) 
			{
				play=1; Ox=1; Oy=1; s=0; H=3;
				for (int i = 1; i < 9; i++)
                {
                    for (int j = 1; j <= 43; j++)
                    {
                        map[i][j] = ' '; map[1][1] = 'O';
                    }
                }
				
			}
			
		}
    }
    
}

